from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SessionItem(BaseModel):
    time_slot: str
    duration_minutes: int = Field(..., gt=0)
    class_name: str = Field(..., min_length=1, max_length=50)
    required_teachers_count: int = Field(..., ge=1)


class SchoolItem(BaseModel):
    school_name: str = Field(..., min_length=1, max_length=150)
    sessions: List[SessionItem]


class GenerateOptions(BaseModel):
    available_teachers: List[str]
    replace_day: bool = False              # True: kosongkan hari itu dulu
    continuity: bool = True                # sedikit mungkin guru berbeda per sekolah
    teacher_priority: Dict[str, int] = {}  # {"Mr Tama": 5} 1..5, default 3
    max_daily_minutes: Optional[int] = Field(None, gt=0)
    max_weekly_minutes: Optional[int] = Field(None, gt=0)


class ScheduleRequest(GenerateOptions):
    day: str
    schools: List[SchoolItem]


class DaySchedule(BaseModel):
    day: str
    schools: List[SchoolItem]


class MultiDayRequest(GenerateOptions):
    days: List[DaySchedule]


class ManualScheduleRequest(BaseModel):
    day: str
    school_name: str
    class_name: str
    time_slot: str                      # "07:00-08:30"
    teachers: List[str]
    required_teachers_count: Optional[int] = None


class SessionUpdate(BaseModel):
    day: Optional[str] = None
    school_name: Optional[str] = None
    class_name: Optional[str] = None
    time_slot: Optional[str] = None
    teachers: Optional[List[str]] = None
    required_teachers_count: Optional[int] = None
