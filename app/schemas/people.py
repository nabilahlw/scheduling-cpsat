from typing import List

from pydantic import BaseModel


class NameBody(BaseModel):
    name: str
    confirm_new: bool = False  # lewati peringatan "nama mirip guru lain"


class AvailabilityItem(BaseModel):
    teacher_name: str
    day: str
    ranges: List[List[str]]  # [["07:00","10:00"],["13:00","16:00"]]
