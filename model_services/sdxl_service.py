import asyncio
import time

from fastapi import HTTPException
from domain.image_generate_request import ImageGenerateRequest
from model_services.base_model import BaseModel
from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.helpers import log_execution_time
from utils.image_manager import ImageManager
from utils.logger import TTLogger
from multiprocessing import Process, Queue

class SDXLService(BaseModel):

    @log_execution_time("Task queue init")
    def __init__(self):
        self.isReady = False
        self.maxWorkerSize = 1
        self.task_queue = Queue(4)
        self.maxWorkerSize = 1
        self.result_futures = {}
        self.result_queue = Queue()
        self.workers = []
        self.logger = TTLogger()
        self.imageManager = ImageManager("img")
        # init queue
        self.task_queue = Queue(4)
        self.listener_task_ref = None
        self.listener_running = True
        # init sdxl runner

    @log_execution_time("Scheduler image processing")
    def processImage(self, imageGenerateRequest: ImageGenerateRequest) -> str:
        if (self.task_queue.full()):
            raise HTTPException(500, "Task queue is full")
        self.task_queue.put((imageGenerateRequest))
        # self.checkIsModelReady()
        # start = time.perf_counter()
        # ImageGenerateTask.model_construct()
        # generateImageTask = ImageGenerateTask.from_request(imageGenerateRequest)
        # taskCompletionSignal = await self.addTask(generateImageTask)
        # TODO await completion
        # TODO add adding and handling withn a queue, this is a shortcut
        # images = self.tt_sdxl_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
        # # TODO add adding and handling withn a queue, this is a shortcut
        # # await taskCompletionSignal
        # end = time.perf_counter()

        # self.logger.logTime(start, end, "Inference time:")
        # return self.imageManager.convertImageToBytes(images[0])

    def isModelReady(self) -> bool:
        return self.isReady

    def checkIsModelReady(self):
        if (self.isModelReady() is not True):
            raise HTTPException(405, "Model is not ready")

    @log_execution_time("Workes creation")
    def startWorkers(self):
        # keep result listener in the main event loop
        self.listener_task_ref = asyncio.create_task(self.result_listener())

        # Spawn one process per worker
        for i in range(self.maxWorkerSize):
            p = Process(target=worker, args=(i, self.task_queue, self.result_queue))
            p.start()
            self.workers.append(p)

    async def result_listener(self):
        while self.listener_running:
            task_id, image = await asyncio.to_thread(self.result_queue.get)
            future = self.result_futures.pop(task_id, None)
            if future:
                future.set_result(image)

    def stopWorkers(self):
        self.logger.info("Stopping workers")
        self.listener_running = False
        # Unblock result_listener if it's waiting
        self.result_queue.put((None, None))
        if self.listener_task_ref:
            self.listener_task_ref.cancel()
        for worker in self.workers:
            self.task_queue.put(None)
            worker.kill()
            worker.join()
        self.workers.clear()
        # Clean up queueus
        self.task_queue.close()
        self.task_queue.join_thread()
        self.result_queue.close()
        self.result_queue.join_thread()
        self.result_futures.clear()
        self.isReady = False
        self.logger.info("Workers stopped")

def worker(worker_id, task_queue: Queue, result_queue):
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