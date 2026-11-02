"""The strict template every model answer must fit.

One answer = one step: an action, a target (element number) and a value.
Anything that doesn't fit is rejected before the hands touch the page.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

# The only actions VisionPilot's hands know how to do.
Action = Literal["click", "type", "select", "scroll", "done"]


class Step(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)  # accept 80 as "80"

    action: Action
    element_id: Optional[int] = None   # the number from the eyes; empty for scroll/done
    value: Optional[str] = None        # text to type, option to pick, or the final answer
    reason: str                        # one short sentence: why this step
    risky: bool = False                # true if it saves, submits or deletes
