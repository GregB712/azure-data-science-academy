"""FastAPI forecast service for the retail demand platform (Module 6).

Two responsibilities:
  - GET  /forecast/{store_id}/{product_id}: return the precomputed weekly forecast
    from the gold/demand_forecast product (the fast, cheap path).
  - POST /score: recompute a single series' next-week forecast with what-if
    planning inputs (e.g. a promotion), reusing the exact feature construction
    and model from forecasting.score.

Storage access is identity-based (DefaultAzureCredential / managed identity in
Container Apps); no keys. See the Module 6 online-endpoints lesson.
"""

from .app import create_app

__all__ = ["create_app"]
