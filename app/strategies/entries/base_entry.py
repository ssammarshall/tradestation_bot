from typing import Protocol

class BaseEntry(Protocol):
    def is_valid(self) -> bool:
        """Check if the entry is valid and can be executed."""
        ...