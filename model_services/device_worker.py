from asyncio import Queue
import asyncio

from tt_model_runners.base_device_runner import DeviceRunner
from tt_model_runners.runner_fabric import get_device_runner
from utils.image_manager import ImageManager
from utils.logger import TTLogger


def device_worker(worker_id: str, task_queue: Queue, result_queue: Queue, warmup_signals_queue: Queue):
    device_runner: DeviceRunner = get_device_runner()
    logger = TTLogger()
    asyncio.run(device_runner.load_model())
    warmup_signals_queue.put(worker_id)
    while True:
        imageGenerateRequest = task_queue.get()
        if imageGenerateRequest is None:  # Sentinel to shut down
            device_runner.close_device()
            break
        logger.debug(f"Worker {worker_id} processing task: {imageGenerateRequest}")
        # ToDo check do we need to move this to event loop
        # this way we get multiprocessing but we lose model agnostic worker
        # Option 2: have a custom processor 
        images = device_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
        logger.debug(f"Worker {worker_id} finished processing task: {imageGenerateRequest}")
        image = ImageManager("img").convertImageToBytes(images[0])
        # add to result queue since we cannot use future in multiprocessing
        result_queue.put((imageGenerateRequest._task_id, image))