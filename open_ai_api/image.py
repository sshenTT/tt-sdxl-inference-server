from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from domain.image_generate_request import ImageGenerateRequest
from domain.output_format import OutputFormat
from model_services.base_model import BaseModel
from resolver.model_resolver import model_resolver
from utils.image_manager import ImageManager

router = APIRouter()


@router.post('/generations')
async def generateImage(imageGenerateRequest: ImageGenerateRequest, service: BaseModel = Depends(model_resolver)):
    return await service.processImage(imageGenerateRequest)

### 📤 Download Endpoint
@router.get("/download/{filename}")
async def download_image(filename: str):
    file_path = ImageManager().get_image_path(filename)
    return FileResponse(file_path, media_type="image/jpeg")

@router.get('/tt-liveness')
def liveness(service: BaseModel = Depends(model_resolver)):
    return {'status': 'alive', 'is_ready': service.isModelReady()}

@router.get('/tt-warm-up-model')
async def warmUpModel(service: BaseModel = Depends(model_resolver)):
    return await service.warmupModel()

### 📥 Upload Endpoint
@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    filename = ImageManager().save_image(file)
    return {"message": f"{filename} saved successfully"}

### 🗑️ Delete Endpoint
@router.delete("/delete/{filename}")
async def delete_image(filename: str):
    message = ImageManager().delete_image(filename)
    return {"message": message}