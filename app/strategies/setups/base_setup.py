from typing import Protocol

class BaseSetup(Protocol):
    def is_valid(self) -> bool:
        """Check if the setup is valid and can be executed."""
        ...