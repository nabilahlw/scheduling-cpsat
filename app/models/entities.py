"""Entitas domain sederhana (dataclass)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    role: str
    is_active: bool

    @classmethod
    def from_row(cls, r) -> "User":
        return cls(r[0], r[1], r[2], bool(r[3]))

    def to_dict(self) -> dict:
        return {"id": self.id, "username": self.username, "role": self.role,
                "is_active": self.is_active}


@dataclass
class NamedRecord:
    id: int
    name: str
    deleted_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, r):
        return cls(r[0], r[1], r[2])

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None}


class Teacher(NamedRecord):
    pass


class School(NamedRecord):
    pass
