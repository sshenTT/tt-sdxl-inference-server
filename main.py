import os
from fastapi import FastAPI
from open_ai_api import api_router


env = os.getenv("ENVIRONMENT", "production")
model = os.getenv("MODEL_IN_USE", "SDXL-3.5")
# TODO load proper development later
env = "development"

app = FastAPI(
    title="TT inference server",
    description=f"Inferencing API currently serving {model} model",
    docs_url="/docs" if env == "development" else None,
    redoc_url="/redoc" if env == "development" else None,
    openapi_url="/openapi.json" if env == "development" else None,
    version="0.0.1"
)
app.include_router(api_router)
