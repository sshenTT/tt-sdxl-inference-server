# class TaskWorker:
#     def __init__(self, worker_id, task_queue: Queue, result_queue: Queue):
#         self.worker_id = worker_id
#         self.task_queue = task_queue
#         self.result_queue = result_queue

#     def run(self):
#         asyncio.run(self.tt_sdxl_runner.load_model())
#         while True:
#             imageGenerateRequest = self.task_queue.get()
#             if imageGenerateRequest is None:
#                 break
#             images = self.tt_sdxl_runner.runInference(imageGenerateRequest.prompt, imageGenerateRequest.num_inference_step)
#             image = self.imageManager.convertImageToBytes(images[0])
#             # add to result queue since we cannot use future in multiprocessing
#             self.result_queue.put((imageGenerateRequest._task_id, image))