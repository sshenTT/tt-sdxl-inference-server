import uuid
from pydantic import BaseModel, Field

# from domain.output_format import OutputFormat

class ImageGenerateRequest(BaseModel):
    prompt: str
    # output_format: OutputFormat
    num_inference_step: int = Field(..., ge=20, le=50)

# class ImageGenerateTask(ImageGenerateRequest):
#     fileName: str

#     @classmethod
#     def from_request(cls, req: ImageGenerateRequest):
#         return cls(
#             prompt=req.prompt,
#             output_format=req.output_format,
#             fileName=str(uuid.uuid4())
#         )