from asyncio import Queue
import asyncio

from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.image_manager import ImageManager
from utils.logger import TTLogger


def device_worker(worker_id: str, task_queue: Queue, result_queue: Queue, warmup_signals_queue: Queue):
    tt_sdxl_runner = TTSDXLRunner()
    logger = TTLogger()
    asyncio.run(tt_sdxl_runner.load_model())
    warmup_signals_queue.put(worker_id)
    while True:
        imageGenerateRequest = task_queue.get()
        if imageGenerateRequest is None:  # Sentinel to shut down
            tt_sdxl_runner.close_device()
            break
        logger.debug(f"Worker {worker_id} processing task: {imageGenerateRequest}")
        images = tt_sdxl_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
        logger.debug(f"Worker {worker_id} finished processing task: {imageGenerateRequest}")
        image = ImageManager("img").convertImageToBytes(images[0])
        # add to result queue since we cannot use future in multiprocessing
        result_queue.put((imageGenerateRequest._task_id, image))