import multiprocessing
from multiprocessing.managers import BaseManager

class ProcessManager:
    _manager : BaseManager
    _managed_objects : dict[str, any] = {}
    _subprocesses : dict[str, multiprocessing.Process] = {}


    def __init__(self):
        self._register_proxy_classes()
        self._manager = BaseManager()
        self._manager.start()
        self._create_managed_objects()


    def _register_proxy_classes(self):
        BaseManager.register('dict', dict)


    def _create_managed_objects(self):
        acquisition_states = self._manager.__dict__
