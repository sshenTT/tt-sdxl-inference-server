import os
from model_services.base_model import BaseModel
from model_services.sdxl_service import SDXLService
# from model_services.task_worker import TaskWorker

# model and worker are singleton
current_model_holder = None
current_worker_holder = None

def model_resolver() -> BaseModel:
    global current_model_holder
    env = os.getenv("MODEL_IN_USE", "SDXL-3.5")
    if env == "SDXL-3.5":
        if (current_model_holder is None):
            current_model_holder = SDXLService()
        return current_model_holder    
    return BaseModel()

# def worker_resolver() -> TaskWorker:
#     global current_worker_holder
#     if (current_worker_holder is None):
#         current_worker_holder = TaskWorker()
#     return current_worker_holder