"""FastAPI app factory for the forecast service.

Configuration (environment variables, all with local defaults for development):
  FORECAST_TABLE  Delta path/URI of gold/demand_forecast (precomputed forecasts)
  GOLD_TABLE      Delta path/URI of gold/weekly_demand_features (for on-demand)
  MODEL_PATH      model.txt (or a directory containing it) for on-demand scoring

Run locally (WSL / Python), from code/:
    FORECAST_TABLE=../data/lake/gold/demand_forecast \
    GOLD_TABLE=../data/lake/gold/weekly_demand_features \
    MODEL_PATH=../data/model/model/model.txt \
    uvicorn forecast_service.app:app --reload
"""

from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd
from deltalake import DeltaTable
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from forecasting.score import build_scoring_frame, load_model, predict_rows
from forecasting.train import _storage_options


class ScoreRequest(BaseModel):
    store_id: str
    product_id: str
    promo_days: int | None = Field(default=None, ge=0, le=7)
    holiday_days: int | None = Field(default=None, ge=0, le=7)
    avg_price: float | None = Field(default=None, gt=0)


class ForecastResponse(BaseModel):
    store_id: str
    product_id: str
    week_start: str
    forecast_units: float
    source: str  # "precomputed" or "on-demand"


def create_app() -> FastAPI:
    app = FastAPI(title="Retail Demand Forecast Service", version="1.0.0")

    forecast_table = os.environ.get("FORECAST_TABLE", "../data/lake/gold/demand_forecast")
    gold_table = os.environ.get("GOLD_TABLE", "../data/lake/gold/weekly_demand_features")
    model_path = os.environ.get("MODEL_PATH", "../data/model/model/model.txt")

    @lru_cache(maxsize=1)
    def precomputed() -> pd.DataFrame:
        df = DeltaTable(forecast_table, storage_options=_storage_options(forecast_table)).to_pandas()
        return df.astype({"store_id": str, "product_id": str})

    @lru_cache(maxsize=1)
    def scoring_frame() -> pd.DataFrame:
        gold = DeltaTable(gold_table, storage_options=_storage_options(gold_table)).to_pandas()
        frame = build_scoring_frame(gold)
        frame["store_id_str"] = frame["store_id"].astype(str)
        frame["product_id_str"] = frame["product_id"].astype(str)
        return frame

    @lru_cache(maxsize=1)
    def model():
        return load_model(model_path)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/forecast/{store_id}/{product_id}", response_model=ForecastResponse)
    def get_forecast(store_id: str, product_id: str) -> ForecastResponse:
        df = precomputed()
        row = df[(df["store_id"] == store_id) & (df["product_id"] == product_id)]
        if row.empty:
            raise HTTPException(status_code=404, detail="No forecast for that series")
        r = row.iloc[-1]
        return ForecastResponse(store_id=store_id, product_id=product_id,
                                week_start=str(r["week_start"]),
                                forecast_units=float(r["forecast_units"]), source="precomputed")

    @app.post("/score", response_model=ForecastResponse)
    def score_on_demand(req: ScoreRequest) -> ForecastResponse:
        frame = scoring_frame()
        sel = frame[(frame["store_id_str"] == req.store_id)
                    & (frame["product_id_str"] == req.product_id)].copy()
        if sel.empty:
            raise HTTPException(status_code=404, detail="Unknown series (no history)")
        if req.promo_days is not None:
            sel["promo_days"] = req.promo_days
        if req.holiday_days is not None:
            sel["holiday_days"] = req.holiday_days
        if req.avg_price is not None:
            sel["avg_price"] = req.avg_price
        pred = float(predict_rows(model(), sel)[0])
        return ForecastResponse(store_id=req.store_id, product_id=req.product_id,
                                week_start=str(pd.to_datetime(sel["week_start"].iloc[0]).date()),
                                forecast_units=round(pred, 2), source="on-demand")

    return app


app = create_app()
