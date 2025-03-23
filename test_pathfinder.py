from dataclasses import dataclass
from typing import Optional
from pathfinder import BusStop, Pathfinder
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
    expected_path: list[BusStop]
    expected_cost: float
    optimize: str = "t"

    start_line: Optional[str] = None
    minute_cost: int = 1
    transfer_cost: int = 5
    km_cost: int = 0


@pytest.mark.parametrize(
    "params",
    [
        # Is it working at all
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
            ],
            start="a",
            end="b",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
            ],
            expected_cost=15,
            minute_cost=1,
        ),
        # Start time before departure, cost calculated correctly
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
            ],
            start="a",
            end="b",
            at="8:45",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
            ],
            expected_cost=30,
            minute_cost=1,
        ),
        # Multiple stops on the way
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("b", "c", "9:15", "9:30", "101"),
                rowentry("c", "d", "9:30", "9:45", "101"),
            ],
            start="a",
            end="d",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
                BusStop("b", "09:15", "c", "09:30", "101"),
                BusStop("c", "09:30", "d", "09:45", "101"),
            ],
            expected_cost=45,
            minute_cost=1,
        ),
        # Roundabout way is faster
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("b", "c", "9:15", "9:30", "101"),
                rowentry("c", "d", "9:30", "9:45", "101"),
                rowentry("a", "d", "9:00", "9:50", "101"),
            ],
            start="a",
            end="d",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
                BusStop("b", "09:15", "c", "09:30", "101"),
                BusStop("c", "09:30", "d", "09:45", "101"),
            ],
            expected_cost=45,
            minute_cost=1,
        ),
        # Direct but later path is faster
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("b", "c", "9:15", "9:30", "101"),
                rowentry("c", "d", "9:30", "9:45", "101"),
                rowentry("a", "d", "9:05", "9:40", "101"),
            ],
            start="a",
            end="d",
            at="9:00",
            expected_path=[
                BusStop("a", "09:05", "d", "09:40", "101"),
            ],
            expected_cost=40,
            minute_cost=1,
        ),
        # Transfer cost is correct
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("b", "c", "9:15", "9:30", "222"),
            ],
            start="a",
            end="c",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
                BusStop("b", "09:15", "c", "09:30", "222"),
            ],
            expected_cost=130,
            minute_cost=1,
            transfer_cost=100,
        ),
        # Prefers slower path, but without transfers
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("b", "c", "9:15", "9:30", "101"),
                rowentry("a", "d", "9:05", "9:10", "101"),
                rowentry("d", "c", "9:10", "9:20", "222"),
            ],
            start="a",
            end="c",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
                BusStop("b", "09:15", "c", "09:30", "101"),
            ],
            expected_cost=30,
            minute_cost=1,
            transfer_cost=100,
        ),
        # When starting on some line, prefer that line instead of transfering
        PathfinderTestParams(
            nodes=[
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:00", "9:10", "222"),
            ],
            start="a",
            start_line="101",
            end="b",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
            ],
            expected_cost=15,
            minute_cost=1,
            transfer_cost=100,
        ),
        # Picks slower path when heuristic is enabled
        PathfinderTestParams(
            nodes=[
                rowentry(
                    "a", "b", "9:00", "9:15", "101", a_coords=(0, 0), b_coords=(100, 0)
                ),
                rowentry(
                    "b",
                    "c",
                    "9:15",
                    "9:30",
                    "101",
                    a_coords=(100, 0),
                    b_coords=(101, 0),
                ),
                rowentry(
                    "a", "d", "9:05", "9:10", "101", a_coords=(0, 0), b_coords=(1, 0)
                ),
                rowentry(
                    "d", "c", "9:10", "9:20", "101", a_coords=(1, 0), b_coords=(101, 0)
                ),
            ],
            start="a",
            end="c",
            at="9:00",
            expected_path=[
                BusStop("a", "09:00", "b", "09:15", "101"),
                BusStop("b", "09:15", "c", "09:30", "101"),
            ],
            expected_cost=30,
            minute_cost=1,
            km_cost=1000,
        ),
    ],
)
def test_path(params: PathfinderTestParams):
    pathfinder = Pathfinder(params.nodes)
    result = pathfinder.find_path(
        start=params.start,
        end=params.end,
        time=params.at,
        starting_line=params.start_line,
        minute_cost=params.minute_cost,
        transfer_cost=params.transfer_cost,
        km_cost=params.km_cost,
    )
    assert result is not None

    path, cost = result

    assert path is not None
    assert cost is not None

    for actual, expected in zip(path, params.expected_path):
        print(path)
        print(expected)
        assert actual == expected
    assert cost == params.expected_cost
