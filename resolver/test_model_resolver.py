from . import model_resolver
from model_services.base_model import BaseModel
from model_services.image_service import ImageService
from model_services.device_worker import TaskWorker

def setup_module(module):
    # Reset singletons before each test module
    model_resolver.current_model_holder = None
    model_resolver.current_worker_holder = None

def teardown_module(module):
    # Reset singletons after each test module
    model_resolver.current_model_holder = None
    model_resolver.current_worker_holder = None

def test_model_resolver_returns_sdxl_service(monkeypatch):
    monkeypatch.setenv("model_service", "image")
    model = model_resolver.model_resolver()
    assert isinstance(model, ImageService)
    # Should return the same instance (singleton)
    model2 = model_resolver.model_resolver()
    assert model is model2

def test_model_resolver_returns_base_model(monkeypatch):
    monkeypatch.setenv("model_service", "OTHER")
    model = model_resolver.model_resolver()
    assert isinstance(model, BaseModel)
    # Should not be ImageService
    assert not isinstance(model, ImageService)

def test_worker_resolver_returns_task_worker():
    worker = model_resolver.worker_resolver()
    assert isinstance(worker, TaskWorker)
    # Should return the same instance (singleton)
    worker2 = model_resolver.worker_resolver()
    assert worker is worker2