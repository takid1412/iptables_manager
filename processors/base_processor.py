from utils.logger import create_logger

class BaseProcessor:
    def __init__(self):
        self.logger = create_logger(self.__class__.__name__)

    def process(self, config: str) -> str:
        return config