import os
from model_services.base_model import BaseModel
from model_services.sdxl_service import SDXLService

# model is singleton
current_model_holder = None

def model_resolver() -> BaseModel:
    global current_model_holder
    env = os.getenv("MODEL_IN_USE", "SDXL-3.5")
    if env == "SDXL-3.5":
        if (current_model_holder is None):
            current_model_holder = SDXLService()
        return current_model_holder    
    return BaseModel()