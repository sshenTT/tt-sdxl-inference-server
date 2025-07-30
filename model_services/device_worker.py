from queue import Queue
import asyncio

import threading

from domain.image_generate_request import ImageGenerateRequest
from tt_model_runners.base_device_runner import DeviceRunner
from tt_model_runners.runner_fabric import get_device_runner
from utils.image_manager import ImageManager
from utils.logger import TTLogger

def device_worker(worker_id: str, task_queue: Queue, result_queue: Queue, warmup_signals_queue: Queue, error_queue: Queue, device):
    device_runner: DeviceRunner = None
    logger = TTLogger()
    try:
        device_runner: DeviceRunner = get_device_runner(worker_id)
        # Create a new event loop for this thread to avoid conflicts
        # most likely multiple devices will be running this in parallel
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(device_runner.load_model(device))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to get device runner: {e}")
        error_queue.put((worker_id, str(e)))
        return
    logger.info(f"Worker {worker_id} started with device runner: {device_runner}")
    # Signal that this worker is ready after warmup
    warmup_signals_queue.put(worker_id)

    # Main processing loop
    while True:
        imageGenerateRequest: ImageGenerateRequest = task_queue.get()
        if imageGenerateRequest is None:  # Sentinel to shut down
            logger.info(f"Worker {worker_id} shutting down")
            break
        logger.debug(f"Worker {worker_id} processing task: {imageGenerateRequest}")
        # Timebox runInference
        inferencing_timeout = 10 + imageGenerateRequest.num_inference_step * 2  # seconds
        images = None

        inference_successful = False
        timer_ran_out = False
        # TODO revert this since timeout handler does not continue!!!!
        def timeout_handler():
            nonlocal inference_successful, timer_ran_out
            if not inference_successful:
                logger.error(f"Worker {worker_id} task {imageGenerateRequest._task_id} timed out after {inferencing_timeout}s")
                error_msg = f"Worker {worker_id} timed out: {inferencing_timeout}s num inference steps {imageGenerateRequest.num_inference_step}"
                error_queue.put((imageGenerateRequest._task_id, error_msg))
                logger.info("Still waiting for inference to complete, we're not stopping worker {worker_id} ")
                timer_ran_out = True

        timeout_timer = threading.Timer(inferencing_timeout, timeout_handler)
        timeout_timer.start()

        try:
            # Direct call - no thread pool needed since we're already in a thread
            images = device_runner.runInference(
                imageGenerateRequest.prompt,
                imageGenerateRequest.num_inference_step
            )
            inference_successful = True
            timeout_timer.cancel()
                
            if images is None or len(images) == 0:
                error_queue.put((imageGenerateRequest._task_id, "No images generated"))
                continue
                
        except Exception as e:
            timeout_timer.cancel()
            error_msg = f"Worker {worker_id} inference error: {str(e)}"
            logger.error(error_msg)
            error_queue.put((imageGenerateRequest._task_id, error_msg))
            continue

        logger.debug(f"Worker {worker_id} finished processing task: {imageGenerateRequest}")

        # Process result only if timer didn't run out
        # Prevents memory leaks
        if timer_ran_out:
            logger.warning(f"Worker {worker_id} task {imageGenerateRequest._task_id} ran out of time, skipping result processing")
            continue
        try:
            image = ImageManager("img").convertImageToBytes(images[0])
            result_queue.put((imageGenerateRequest._task_id, image))
            logger.debug(f"Worker {worker_id} completed task: {imageGenerateRequest._task_id}")
            
        except Exception as e:
            error_msg = f"Worker {worker_id} image conversion error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            error_queue.put((imageGenerateRequest._task_id, error_msg))
            continue