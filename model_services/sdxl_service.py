import asyncio
import time

from fastapi import HTTPException
from domain.image_generate_request import ImageGenerateRequest, ImageGenerateTask
from model_services.base_model import BaseModel
from tt_model_runners.sdxl_runner import TTSDXLRunner
from utils.image_manager import ImageManager
from utils.logger import TTLogger


class SDXLService(BaseModel):
    isReady = False
    imageManager = None
    maxWorkerSize = 3
    task_queue = None
    tt_sdxl_runner = None

    def __init__(self):
        self.logger = TTLogger()
        self.imageManager = ImageManager("img")
        # init queue
        self.task_queue = asyncio.Queue(self.maxWorkerSize)
        # init sdxl runner
        self.tt_sdxl_runner = TTSDXLRunner()
        # run queue worker async

    async def processImage(self, imageGenerateRequest: ImageGenerateRequest) -> str:
        self.checkIsModelReady()
        start = time.perf_counter()
        ImageGenerateTask.model_construct()
        generateImageTask = ImageGenerateTask.from_request(imageGenerateRequest)
        taskCompletionSignal = await self.addTask(generateImageTask)
        # TODO await completion
        # TODO add adding and handling withn a queue, this is a shortcut
        asyncio.wait_for(self.tt_sdxl_runner.runInference([imageGenerateRequest.prompt]), timeout=20)
        # TODO add adding and handling withn a queue, this is a shortcut
        # await taskCompletionSignal
        end = time.perf_counter()

        image = self.imageManager.base64ConvertImage("tenstorrent_logo.jpg")

        self.logger.logTime(start, end, "Inference time:")
        return image

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
        await asyncio.to_thread(self.run_model_warmup_in_thread)
        await asyncio.to_thread(self.run_worker_in_thread)

    def run_worker_in_thread(self):
        import asyncio
        print("Running worker in thread")
        asyncio.run(self.runWorker())

    def run_model_warmup_in_thread(self):
        import asyncio
        print("Running model warmup in thread")
        device_params = {"l1_small_size": 57344}
        # self.tt_sdxl_runner.mesh_device(device_params, {})
        asyncio.run(self.tt_sdxl_runner.load_model(device_params, {}))
        self.isReady = True

    def isModelReady(self) -> bool:
        self.tt_sdxl_runner.one_step_inference()
        return self.isReady

    def checkIsModelReady(self):
        if (self.isModelReady() is not True):
            raise HTTPException(405, "Model is not ready")

    async def addTask(self, task):
        if (self.task_queue.full()):
            raise HTTPException(500, "Task queue is full")
        taskCompletionIdentifier = asyncio.get_running_loop().create_future()
        #self.task_queue.put((task, taskCompletionIdentifier))
        await self.task_queue.put((self.executeInference(), taskCompletionIdentifier))
        return taskCompletionIdentifier

    async def runWorker(self):
        self.logger.info("Worker is starting")
        while True:
            # TODO find a free device 
            task, completion = await self.task_queue.get()
            await task
            completion = True
            try:
                print(f"Processing task: {task}")
                await asyncio.sleep(1)  # Simulate work
            finally:
                self.task_queue.task_done()
    
    async def executeInference(self):
        asyncio.sleep(10)
        print("inferencing")