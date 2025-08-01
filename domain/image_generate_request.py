from typing import Optional
from pydantic import BaseModel, Field, PrivateAttr

class ImageGenerateRequest(BaseModel):
    prompt: str
    # negative_prompt: Optional[str] = None
    # output_format: OutputFormat
    # num_inference_step: int = Field(..., ge=1, le=50)
    _task_id: str = PrivateAttr()