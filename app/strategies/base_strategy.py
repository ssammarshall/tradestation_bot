from typing import Protocol

class BaseStrategy(Protocol):
    def evaluate(self) -> None:
        """Evaluate the strategy."""
        ...