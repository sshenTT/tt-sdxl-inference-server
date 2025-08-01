from model_services.base_model import BaseModel
from model_services.image_service import ImageService
from config.settings import settings
# from model_services.task_worker import TaskWorker

# model and worker are singleton
current_model_holder = None

def model_resolver() -> BaseModel:
    global current_model_holder
    model_service = settings.model_service
    if model_service == "image":
        if (current_model_holder is None):
            current_model_holder = ImageService()
        return current_model_holder    
    return BaseModel()