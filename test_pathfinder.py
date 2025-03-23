from dataclasses import dataclass
from typing import Optional
from pathfinder import Pathfinder
from graph import RowEntry
import pytest
from datetime import datetime


def to_datetime(time: str):
    if time is None:
        return None
    hour, second = time.split(":")
    day = 1
    hour = int(hour)
    second = int(second)
    if hour >= 24:
        day = 2
        hour -= 24
    return datetime(2000, 1, day, hour, second)


def rowentry(
    a,
    b,
    start: str = "9:00",
    end: str = "9:15",
    bus="A",
    a_coords=(0, 0),
    b_coords=(0, 0),
) -> RowEntry:
    return RowEntry(
        start=a,
        end=b,
        departs_at=to_datetime(start),
        arrives_at=to_datetime(end),
        bus_n=bus,
        start_latitude=a_coords[0],
        start_longitude=a_coords[1],
        end_latitude=b_coords[0],
        end_longitude=b_coords[1],
    )


@dataclass
class ExpectedStop:
    stop_name: str
    time: str
    line: str


@dataclass
class PathfinderTestParams:
    nodes: list[RowEntry]
    start: str
    end: str
    at: str
    expected_path: list[ExpectedStop]
    expected_cost: float
    optimize: str = "t"

    start_line: Optional[str] = None
    minute_cost: int = 1
    transfer_cost: int = 5
    km_cost: int = 0


@pytest.mark.parametrize(
    "params",
    [
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
            ],
            start="a",
            end="b",
            at="9:00",
            expected_path=[
                ExpectedStop("a", "09:00", "101"),
                ExpectedStop("b", "09:15", "101"),
            ],
            expected_cost=15,
            minute_cost=1,
        ),
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
            ],
            start="a",
            end="b",
            at="8:45",
            expected_path=[
                ExpectedStop("a", "09:00", "101"),
                ExpectedStop("b", "09:15", "101"),
            ],
            expected_cost=30,
            minute_cost=1,
        ),
    ],
)
def test_time_weight(params: PathfinderTestParams):
    pathfinder = Pathfinder(params.nodes)
    path, cost = pathfinder.find_path(
        start=params.start,
        end=params.end,
        time=params.at,
        starting_line=params.start_line,
        minute_cost=params.minute_cost,
        transfer_cost=params.transfer_cost,
        km_cost=params.km_cost,
    )

    assert path is not None
    assert cost is not None

    for actual, expected in zip(path, params.expected_path):
        assert actual.stop_name == expected.stop_name
        assert actual.bus_n == expected.line
        assert actual.time == expected.time
    assert cost == params.expected_cost
