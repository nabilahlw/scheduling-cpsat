import pytest

from app.core.errors import BadRequest
from app.lib.names import NameUtil
from app.lib.timeutil import TimeUtil


def test_parse_slot_and_formats():
    assert TimeUtil.parse_slot("07.45-09.00") == (465, 540)
    assert TimeUtil.parse_slot("7:45-09:00") == (465, 540)
    assert TimeUtil.hhmm(465) == "07:45"
    assert TimeUtil.fmt(150) == "2 jam 30 menit"


@pytest.mark.parametrize("bad", ["", "09:00-08:00", "25:00-26:00", "abc", "08:00"])
def test_parse_slot_rejects(bad):
    with pytest.raises(BadRequest):
        TimeUtil.parse_slot(bad)


def test_normalize_day():
    assert TimeUtil.normalize_day("monday") == "SENIN"
    assert TimeUtil.normalize_day(" jumat ") == "JUMAT"
    with pytest.raises(BadRequest):
        TimeUtil.normalize_day("someday")


def test_merge_and_subtract():
    assert TimeUtil.merge_ranges([(60, 120), (120, 180), (300, 360)]) == [(60, 180), (300, 360)]
    assert TimeUtil.subtract([(0, 100)], [(20, 30), (50, 60)]) == [(0, 20), (30, 50), (60, 100)]


def test_similar_names():
    assert NameUtil.similar("Mr Prisca", ["Ms Prisca", "Budi"]) == ["Ms Prisca"]
    assert NameUtil.similar("Budi", ["Budi"]) == []
