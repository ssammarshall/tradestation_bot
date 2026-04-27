from app.schemas.bars import Bar
from app.strategies.setups.base_setup import BaseSetup

class NYIFVGLiquiditySweepSetup(BaseSetup):
    def __init__(self) -> None:
        super().__init__()

    def is_valid(self, bar: Bar) -> bool:
        # Implement the validation logic for the NYIFVGLiquiditySweepSetup
        pass