import asyncio
import time

from fastapi import HTTPException
from fastapi.params import Depends
from config.settings import Settings, get_settings
from domain.image_generate_request import ImageGenerateRequest
from model_services.device_worker import device_worker
from model_services.base_model import BaseModel
from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.helpers import log_execution_time
from utils.image_manager import ImageManager
from utils.logger import TTLogger
from multiprocessing import Process, Queue

class SDXLService(BaseModel):

    @log_execution_time("Task queue init")
    def __init__(self):
        settings = get_settings()
        self.logger = TTLogger()
        self.isReady = False
        self.worker_count = self._getWorkerCount(settings)
        self.task_queue = Queue(self._get_max_queue_size(settings))
        self.result_futures = {}
        self.result_queue = Queue()
        self.workers = []
        self.imageManager = ImageManager("img")
        # init queue
        self.listener_task_ref = None
        self.listener_running = True

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
        for i in range(self.worker_count):
            p = Process(target=device_worker, args=(i, self.task_queue, self.result_queue))
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
    
    def _getWorkerCount(self, setttings: Settings) -> int:
        try:
            workerCount = len(setttings.device_ids.split(","))
            if workerCount < 1:
                self.logger.error("Worker count is 0")
                raise ValueError("Worker count must be at least 1")
            return workerCount
        except Exception as e:
            self.logger.error(f"Erros getting workers cannot: {e}")
            raise HTTPException(status_code=500, detail="Workers cannot be initialized")
    
    def _get_max_queue_size(self, settings: Settings) -> int:
        try:
            max_queue_size = settings.max_queue_size
            if max_queue_size < 1:
                self.logger.error("Max queue size is 0")
                raise ValueError("Max queue size must be at least 1")
            return max_queue_size
        except Exception as e:
            self.logger.error(f"Error getting max queue size: {e}")
            raise HTTPException(status_code=500, detail="Max queue size not provided in settings")