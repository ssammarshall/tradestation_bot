from abc import ABC, abstractmethod


class BaseSetup(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def is_valid(self) -> bool: ...
