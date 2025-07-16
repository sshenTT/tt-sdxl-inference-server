from fastapi import HTTPException

from domain.image_generate_request import ImageGenerateRequest


class BaseModel:
    def processImage(self, imageGenerateRequest: ImageGenerateRequest):
        return NotImplementedError("Method not implemented")

    def isModelReady(self) -> bool:
        return NotImplementedError("Method not implemented")

    async def warmupModel(self):
        return NotImplementedError("Method not implemented")

    def completions(self):
        raise HTTPException(501, "Method not implemented")