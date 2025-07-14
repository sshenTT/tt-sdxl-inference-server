import uuid
from pydantic import BaseModel

from domain.output_format import OutputFormat

class ImageGenerateRequest(BaseModel):
    prompt: str
    output_format: OutputFormat

class ImageGenerateTask(ImageGenerateRequest):
    fileName: str

    @classmethod
    def from_request(cls, req: ImageGenerateRequest):
        return cls(
            prompt=req.prompt,
            output_format=req.output_format,
            fileName=str(uuid.uuid4())
        )