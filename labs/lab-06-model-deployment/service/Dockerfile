# Image for the FastAPI forecast service (code/forecast_service).
# Build with the academy code/ folder as the build context so the forecasting
# and forecast_service packages are both present:
#   docker build -f labs/lab-06-model-deployment/service/Dockerfile -t demand-forecast-api ./code
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Bake the trained model into the image (copy ../data/model/model/model.txt into
# code/forecast_service/model.txt before building, or download it at startup).
ENV MODEL_PATH=/app/forecast_service/model.txt
ENV PORT=8000
EXPOSE 8000

# Reads the forecast/feature tables from ADLS Gen2 by managed identity at runtime.
CMD ["sh", "-c", "uvicorn forecast_service.app:app --host 0.0.0.0 --port ${PORT}"]
