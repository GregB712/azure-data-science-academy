"""Synthetic retail demand dataset for the Azure Data Science Academy.

Generates a realistic-looking multi-store, multi-product daily sales history with
prices, promotions, holidays, store attributes and stock-outs. The output mimics
what a retail organisation's source systems would export, so it can be used as
*raw* input for the Bronze layer of the lakehouse labs and the capstone.

Outputs (under --out, default ./data/raw):
    stores.csv                      store master data (CSV, like an ERP export)
    products.json                   product master data (JSON lines, like an API dump)
    calendar.csv                    calendar with holidays
    pos_sales/pos_sales_YYYY-MM.csv one file per month (like a nightly POS extract)

Design notes
- Demand = base level x store size x weekly/yearly seasonality x trend
           x promo lift x holiday lift x price elasticity, sampled from a
  negative binomial (over-dispersed counts, many zeros for slow movers).
- Sales are *censored* by stock: units_sold = min(demand, stock_on_hand).
  Forecasting on censored sales without the stockout flag biases models low,
  which is a realistic trap the capstone discusses.
- Optional, deterministic data-quality defects (--dq-defect-rate) give the
  Silver layer something real to validate: duplicate rows, negative units,
  missing prices and unknown store IDs.

Run (WSL / Python):
    python generate.py --out ./data/raw --stores 10 --products 40 \
        --start 2024-01-01 --end 2025-12-31 --seed 42
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

CATEGORIES = {
    # category: (subcategories, base daily units per store, price range, weekly profile Mon..Sun)
    "Fresh": (["Bakery", "Dairy", "Produce"], 14.0, (0.8, 4.5), [0.9, 0.85, 0.9, 0.95, 1.1, 1.35, 1.0]),
    "Grocery": (["Pantry", "Snacks", "Beverages"], 8.0, (1.0, 6.0), [0.9, 0.9, 0.9, 1.0, 1.1, 1.3, 0.9]),
    "Household": (["Cleaning", "Paper"], 3.0, (2.0, 12.0), [0.95, 0.95, 0.95, 1.0, 1.05, 1.25, 0.85]),
    "Electronics": (["Accessories", "Small Appliances"], 0.6, (10.0, 120.0), [0.8, 0.8, 0.85, 0.9, 1.1, 1.5, 1.05]),
    "Seasonal": (["Garden", "Holiday Decor"], 1.2, (3.0, 40.0), [0.85, 0.85, 0.9, 0.95, 1.1, 1.45, 0.9]),
}

REGIONS = [
    ("North", "Hamburg", 53.55, 9.99),
    ("North", "Bremen", 53.08, 8.80),
    ("West", "Cologne", 50.94, 6.96),
    ("West", "Dusseldorf", 51.23, 6.78),
    ("South", "Munich", 48.14, 11.58),
    ("South", "Stuttgart", 48.78, 9.18),
    ("East", "Berlin", 52.52, 13.40),
    ("East", "Leipzig", 51.34, 12.37),
    ("Central", "Frankfurt", 50.11, 8.68),
    ("Central", "Kassel", 51.31, 9.48),
]


def easter_sunday(year: int) -> date:
    """Anonymous Gregorian algorithm (Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def black_friday(year: int) -> date:
    """Day after the fourth Thursday of November."""
    nov1 = date(year, 11, 1)
    first_thu = nov1 + timedelta(days=(3 - nov1.weekday()) % 7)
    return first_thu + timedelta(days=21 + 1)


def holidays_for(year: int) -> dict[date, tuple[str, float, bool]]:
    """date -> (name, demand multiplier, stores_closed)."""
    easter = easter_sunday(year)
    return {
        date(year, 1, 1): ("New Year's Day", 0.0, True),
        easter - timedelta(days=2): ("Good Friday", 0.0, True),
        easter - timedelta(days=1): ("Easter Saturday", 1.6, False),
        easter + timedelta(days=1): ("Easter Monday", 0.0, True),
        date(year, 5, 1): ("Labour Day", 0.0, True),
        black_friday(year): ("Black Friday", 1.5, False),
        date(year, 12, 23): ("Pre-Christmas", 1.7, False),
        date(year, 12, 24): ("Christmas Eve", 1.4, False),
        date(year, 12, 25): ("Christmas Day", 0.0, True),
        date(year, 12, 26): ("Boxing Day", 0.0, True),
        date(year, 12, 31): ("New Year's Eve", 1.3, False),
    }


@dataclass(frozen=True)
class Config:
    out: Path
    n_stores: int = 10
    n_products: int = 40
    start: date = date(2024, 1, 1)
    end: date = date(2025, 12, 31)
    seed: int = 42
    dq_defect_rate: float = 0.002


def make_stores(cfg: Config, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(cfg.n_stores):
        region, city, lat, lon = REGIONS[i % len(REGIONS)]
        size = int(rng.choice([800, 1200, 1800, 2500, 4000], p=[0.15, 0.3, 0.3, 0.15, 0.1]))
        rows.append(
            {
                "store_id": f"S{i + 1:03d}",
                "store_name": f"{city} {['Central', 'Mall', 'Station', 'Park'][i % 4]}",
                "city": city,
                "region": region,
                "country": "DE",
                "latitude": round(lat + rng.normal(0, 0.02), 5),
                "longitude": round(lon + rng.normal(0, 0.02), 5),
                "store_size_sqm": size,
                "store_type": "hypermarket" if size >= 2500 else ("supermarket" if size >= 1200 else "convenience"),
                "opened_date": (cfg.start - timedelta(days=int(rng.integers(400, 4000)))).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def make_products(cfg: Config, rng: np.random.Generator) -> pd.DataFrame:
    cats = list(CATEGORIES)
    rows = []
    for j in range(cfg.n_products):
        cat = cats[j % len(cats)]
        subs, base, (pmin, pmax), _ = CATEGORIES[cat]
        sub = str(rng.choice(subs))
        rows.append(
            {
                "product_id": f"P{j + 1:04d}",
                "product_name": f"{sub} item {j + 1}",
                "category": cat,
                "subcategory": sub,
                "list_price": round(float(rng.uniform(pmin, pmax)), 2),
                "price_elasticity": round(float(rng.uniform(-2.5, -0.8)), 3),
                "popularity": round(float(rng.lognormal(0, 0.6)), 3),
                "is_perishable": cat == "Fresh",
            }
        )
    return pd.DataFrame(rows)


def make_calendar(cfg: Config) -> pd.DataFrame:
    days = pd.date_range(cfg.start, cfg.end, freq="D")
    hol: dict[date, tuple[str, float, bool]] = {}
    for y in range(cfg.start.year, cfg.end.year + 1):
        hol.update(holidays_for(y))
    cal = pd.DataFrame({"date": days.date})
    cal["day_of_week"] = days.dayofweek
    cal["iso_week"] = days.isocalendar().week.to_numpy()
    cal["month"] = days.month
    cal["year"] = days.year
    cal["is_weekend"] = cal["day_of_week"] >= 5
    cal["holiday_name"] = [hol.get(d, ("", 1.0, False))[0] for d in cal["date"]]
    cal["is_holiday"] = cal["holiday_name"] != ""
    cal["stores_closed"] = [hol.get(d, ("", 1.0, False))[2] or (d.weekday() == 6) for d in cal["date"]]
    cal["holiday_multiplier"] = [hol.get(d, ("", 1.0, False))[1] for d in cal["date"]]
    return cal


def make_sales(cfg: Config, stores: pd.DataFrame, products: pd.DataFrame, cal: pd.DataFrame,
               rng: np.random.Generator) -> pd.DataFrame:
    n_days, n_s, n_p = len(cal), len(stores), len(products)
    t = np.arange(n_days)
    doy = pd.to_datetime(cal["date"]).dt.dayofyear.to_numpy()

    # Promotions: ~8% of product-weeks, same calendar across stores (chain-wide promo)
    week_idx = t // 7
    promo_week = rng.random((n_p, week_idx.max() + 1)) < 0.08
    promo = promo_week[:, week_idx]  # (n_p, n_days)
    discount = np.where(promo, rng.choice([0.1, 0.2, 0.3], size=promo.shape), 0.0)

    # Price: list price with slow drift (inflation) and promo discount
    drift = 1.0 + 0.03 * (t / 365.0)
    list_price = products["list_price"].to_numpy()[:, None] * drift[None, :]
    price = np.round(list_price * (1 - discount), 2)

    elasticity = products["price_elasticity"].to_numpy()[:, None]
    price_effect = (price / list_price) ** elasticity  # >1 when discounted

    frames = []
    size_factor = (stores["store_size_sqm"].to_numpy() / 1500.0) ** 0.7
    dow = cal["day_of_week"].to_numpy()
    closed = cal["stores_closed"].to_numpy()
    hol_mult = cal["holiday_multiplier"].to_numpy()

    for p_idx, prod in products.iterrows():
        _, base, _, weekly = CATEGORIES[prod["category"]]
        weekly_arr = np.array(weekly)[dow]
        if prod["category"] == "Seasonal":
            yearly = 1.0 + 0.9 * np.sin(2 * np.pi * (doy - 80) / 365.0).clip(-0.7, 1)
        elif prod["category"] == "Electronics":
            yearly = 1.0 + 0.8 * np.exp(-((doy - 345) ** 2) / (2 * 15.0**2))
        else:
            yearly = 1.0 + 0.12 * np.sin(2 * np.pi * (doy - 170) / 365.0)
        trend = 1.0 + rng.normal(0.04, 0.05) * (t / 365.0)
        for s_idx, store in stores.iterrows():
            mu = (base * prod["popularity"] * size_factor[s_idx] * weekly_arr * yearly * trend
                  * hol_mult * price_effect[p_idx])
            mu = np.where(closed, 0.0, np.maximum(mu, 0.0))
            # Negative binomial via gamma-Poisson mixture, dispersion k
            k = 3.0
            lam = rng.gamma(shape=k, scale=np.where(mu > 0, mu / k, 0.0))
            demand = rng.poisson(lam)

            # Simple periodic replenishment -> occasional stock-outs
            stock = np.empty(n_days, dtype=int)
            on_hand = int(mu[:7].sum() * 1.5) + 5
            target = max(int(np.mean(mu) * 4.5) + 3, 4)
            for d in range(n_days):
                if d % 3 == 0:  # delivery every 3 days, with occasional supply hiccups
                    delivered = target - on_hand if rng.random() > 0.08 else 0
                    on_hand += max(delivered, 0)
                stock[d] = on_hand
                on_hand = max(on_hand - demand[d], 0)
            sold = np.minimum(demand, stock)
            frames.append(
                pd.DataFrame(
                    {
                        "date": cal["date"].to_numpy(),
                        "store_id": store["store_id"],
                        "product_id": prod["product_id"],
                        "units_sold": sold,
                        "unit_price": price[p_idx],
                        "on_promotion": promo[p_idx],
                        "promo_discount_pct": (discount[p_idx] * 100).astype(int),
                        "stock_on_hand_open": stock,
                        "stockout": (demand > stock) & ~closed,
                    }
                )
            )
    sales = pd.concat(frames, ignore_index=True)
    closed_dates = set(cal.loc[cal["stores_closed"], "date"])
    sales = sales[~sales["date"].isin(closed_dates)]  # closed stores produce no POS rows
    sales["revenue"] = (sales["units_sold"] * sales["unit_price"]).round(2)
    sales["transaction_source"] = "pos"
    return sales.sort_values(["date", "store_id", "product_id"]).reset_index(drop=True)


def inject_defects(sales: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Deterministically add realistic source-system defects for Silver validation."""
    if rate <= 0:
        return sales
    sales = sales.copy()
    n = len(sales)
    k = max(int(n * rate), 1)
    idx = rng.choice(n, size=4 * k, replace=False)
    neg, nullp, badstore, dup = np.split(idx, 4)
    sales.loc[neg, "units_sold"] = -sales.loc[neg, "units_sold"].abs() - 1
    sales["unit_price"] = sales["unit_price"].astype("float64")
    sales.loc[nullp, "unit_price"] = np.nan
    sales.loc[badstore, "store_id"] = "S999"
    dups = sales.loc[dup]
    return pd.concat([sales, dups], ignore_index=True).sort_values(["date", "store_id", "product_id"]).reset_index(drop=True)


def write_outputs(cfg: Config, stores, products, cal, sales) -> dict[str, int]:
    out = cfg.out
    (out / "pos_sales").mkdir(parents=True, exist_ok=True)
    stores.to_csv(out / "stores.csv", index=False)
    with open(out / "products.json", "w", encoding="utf-8") as fh:
        for rec in products.to_dict(orient="records"):
            fh.write(json.dumps(rec, default=str) + "\n")
    cal.drop(columns=["holiday_multiplier"]).to_csv(out / "calendar.csv", index=False)
    sales = sales.copy()
    sales["_month"] = pd.to_datetime(sales["date"]).dt.strftime("%Y-%m")
    files = 0
    for month, part in sales.groupby("_month"):
        part.drop(columns=["_month"]).to_csv(out / "pos_sales" / f"pos_sales_{month}.csv", index=False)
        files += 1
    return {"stores": len(stores), "products": len(products), "calendar_days": len(cal),
            "sales_rows": len(sales), "sales_files": files}


def generate(cfg: Config) -> dict[str, int]:
    rng = np.random.default_rng(cfg.seed)
    stores = make_stores(cfg, rng)
    products = make_products(cfg, rng)
    cal = make_calendar(cfg)
    sales = make_sales(cfg, stores, products, cal, rng)
    sales = inject_defects(sales, cfg.dq_defect_rate, rng)
    return write_outputs(cfg, stores, products, cal, sales)


def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("data/raw"))
    p.add_argument("--stores", type=int, default=10)
    p.add_argument("--products", type=int, default=40)
    p.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2025, 12, 31))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dq-defect-rate", type=float, default=0.002,
                   help="Fraction of rows per defect type (0 disables). Default 0.002")
    a = p.parse_args(argv)
    return Config(out=a.out, n_stores=a.stores, n_products=a.products, start=a.start, end=a.end,
                  seed=a.seed, dq_defect_rate=a.dq_defect_rate)


if __name__ == "__main__":
    summary = generate(parse_args())
    print(json.dumps(summary, indent=2))
