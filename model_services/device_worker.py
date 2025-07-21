from asyncio import Queue
import asyncio

from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.image_manager import ImageManager


def device_worker(worker_id, task_queue: Queue, result_queue):
    tt_sdxl_runner = TTSDXLRunner()
    asyncio.run(tt_sdxl_runner.load_model())
    while True:
        imageGenerateRequest = task_queue.get()
        if imageGenerateRequest is None:  # Sentinel to shut down
            break
        # self.logger.info(f"Worker {worker_id} processing task: {imageGenerateRequest}")
        images = tt_sdxl_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
        # self.logger.info(f"Worker {worker_id} finished processing task: {imageGenerateRequest}")
        image = ImageManager("img").convertImageToBytes(images[0])
        # add to result queue since we cannot use future in multiprocessing
        result_queue.put((imageGenerateRequest._task_id, image))