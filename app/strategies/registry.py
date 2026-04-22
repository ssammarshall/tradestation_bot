class StrategyRegistry:
    def __init__(self) -> None:
        self._setups: dict[str, object] = {}
        self._entries: dict[str, object] = {}

    def register_setup(self, name: str, handler: object) -> None:
        self._setups[name] = handler

    def register_entry(self, name: str, handler: object) -> None:
        self._entries[name] = handler

    def get_setup(self, name: str) -> object:
        return self._setups[name]

    def get_entry(self, name: str) -> object:
        return self._entries[name]


def build_default_registry() -> StrategyRegistry:
    registry = StrategyRegistry()

    # registry.register_setup("example_setup", ExampleSetup)

    return registry