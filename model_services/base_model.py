from asyncio import Future, Queue
from fastapi import HTTPException

from domain.image_generate_request import ImageGenerateRequest


class BaseModel:
    task_queue = Queue()
    result_futures = {}

    def processImage(self, imageGenerateRequest: ImageGenerateRequest):
        return NotImplementedError("Method not implemented")

    def isModelReady(self) -> bool:
        return NotImplementedError("Method not implemented")

    async def warmupModel(self):
        return NotImplementedError("Method not implemented")

    def completions(self):
        raise HTTPException(501, "Method not implemented")

    def startWorkers(self):
        raise HTTPException(501, "Method not implemented")