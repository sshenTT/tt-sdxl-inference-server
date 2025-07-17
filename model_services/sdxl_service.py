import asyncio
import time

from fastapi import HTTPException
from domain.image_generate_request import ImageGenerateRequest
from model_services.base_model import BaseModel
from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.image_manager import ImageManager
from utils.logger import TTLogger
from multiprocessing import Process, Queue

class SDXLService(BaseModel):
    isReady = False
    imageManager = None
    maxWorkerSize = 1
    task_queue = Queue(maxWorkerSize)
    result_futures = {}
    result_queue = Queue()
    tt_sdxl_runner = None

    def __init__(self):
        self.logger = TTLogger()
        self.imageManager = ImageManager("img")
        # init queue
        self.task_queue = Queue(self.maxWorkerSize)
        # init sdxl runner
        # self.tt_sdxl_runner = TTSDXLRunner()
        # run queue worker async

    def processImage(self, imageGenerateRequest: ImageGenerateRequest) -> str:
        # self.checkIsModelReady()
        self.addTask(imageGenerateRequest)
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

    async def warmupModel(self):
        # run worker
        asyncio.create_task(self.createAsyncReservations())
        # asyncio.to_thread(self.runWorker())
        start = time.perf_counter()
        end = time.perf_counter()

        print("Loading model!!!!!!!")
        # asyncio.to_thread(self.tt_sdxl_runner.load_model())
        self.logger.logTime(start, end, "Model loaded:")
        return True

    async def createAsyncReservations(self):
        print("Deploying worker and starting model warmup")
        asyncio.create_task(self.result_listener())
        await asyncio.to_thread(self.run_model_warmup_in_thread)
        await asyncio.to_thread(self.run_worker_in_thread)

    def run_worker_in_thread(self):
        print("Running worker in thread")
        self.startWorkers()

    def run_model_warmup_in_thread(self):
        import asyncio
        print("Running model warmup in thread")
        # self.tt_sdxl_runner.mesh_device(device_params, {})
        # asyncio.run(self.tt_sdxl_runner.load_model())
        self.isReady = True

    def isModelReady(self) -> bool:
        return self.isReady

    def checkIsModelReady(self):
        if (self.isModelReady() is not True):
            raise HTTPException(405, "Model is not ready")

    def addTask(self, imageGenerateRequest: ImageGenerateRequest):
        if (self.task_queue.full()):
            raise HTTPException(500, "Task queue is full")
        self.task_queue.put((imageGenerateRequest))

    # async def runWorker(self):
    #     self.logger.info("Worker is starting")
    #     while True:
    #         # TODO find a free device 
    #         task, completion = await self.task_queue.get()
    #         await task
    #         completion = True
    #         try:
    #             print(f"Processing task: {task}")
    #             await asyncio.sleep(1)  # Simulate work
    #         finally:
    #             self.task_queue.task_done()

    def worker(self, worker_id, task_queue: Queue, result_queue):
        tt_sdxl_runner = TTSDXLRunner()
        asyncio.run(tt_sdxl_runner.load_model())
        while True:
            imageGenerateRequest = task_queue.get()
            if imageGenerateRequest is None:  # Sentinel to shut down
                break
            self.logger.info(f"Worker {worker_id} processing task: {imageGenerateRequest}")
            images = tt_sdxl_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
            self.logger.info(f"Worker {worker_id} finished processing task: {imageGenerateRequest}")
            # TODO add adding and handling withn a queue, this is a shortcut
            # await taskCompletionSignal
            image = self.imageManager.convertImageToBytes(images[0])
            result_queue.put((imageGenerateRequest._task_id, image))
    
    def startWorkers(self):
        asyncio.create_task(self.result_listener())
        workers = []

        # Spawn one process per worker
        for i in range(self.maxWorkerSize):
            p = Process(target=self.worker, args=(i, self.task_queue, self.result_queue))
            p.start()
            workers.append(p)
        # Send tasks
        # for task in range(10):
        #     task_queue.put(task)

        # Send shutdown signals
        # for _ in workers:
        #     task_queue.put(None)

        # Collect results
        # for _ in range(10):
        #     print(result_queue.get())

        # Join workers
        # for p in workers:
        #     p.join()

    async def result_listener(self):
        while True:
            task_id, image = await asyncio.to_thread(self.result_queue.get)
            future = self.result_futures.pop(task_id, None)
            if future:
                future.set_result(image)