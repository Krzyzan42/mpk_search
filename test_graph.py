import pytest
from graph import Graph, RowEntry
from datetime import datetime


def to_datetime(time: str):
    hour, second = time.split(":")
    day = 1
    hour = int(hour)
    second = int(second)
    if hour >= 24:
        day = 2
        hour -= 24
    return datetime(2000, 1, day, hour, second)


def rowentry(a, b, start: str, end: str, bus="A") -> RowEntry:
    return RowEntry(
        start=a,
        end=b,
        departs_at=to_datetime(start),
        arrives_at=to_datetime(end),
        bus_n=bus,
    )


@pytest.mark.parametrize(
    "entries, node, expected",
    [
        (
            [rowentry("a", "b", "9:00", "9:10"), rowentry("b", "c", "9:00", "9:10")],
            "b",
            {"c"},
        ),
        (
            [rowentry("a", "b", "9:00", "9:10"), rowentry("b", "a", "9:00", "9:10")],
            "b",
            {"a"},
        ),
        (
            [rowentry("a", "b", "9:00", "9:10"), rowentry("b", "a", "9:00", "9:10")],
            "a",
            {"b"},
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:10"),
                rowentry("c", "b", "9:00", "9:10"),
                rowentry("d", "b", "9:00", "9:10"),
                rowentry("e", "b", "9:00", "9:10"),
            ],
            "b",
            set(),
        ),
        (
            [
                rowentry("b", "a", "9:00", "9:10"),
                rowentry("b", "c", "9:00", "9:10"),
                rowentry("b", "d", "9:00", "9:10"),
                rowentry("b", "e", "9:00", "9:10"),
            ],
            "b",
            {"a", "c", "d", "e"},
        ),
        ([rowentry("b", "b", "9:00", "9:10")], "b", set()),
    ],
)
def test_neighbours(entries, node, expected):
    g = Graph(entries)
    assert set(g.get_neighbouring_nodes(node)) == expected


@pytest.mark.parametrize(
    "connections, start, end, departure_time, expected_arrival_time",
    [
        ([rowentry("a", "b", "9:00", "9:10")], "a", "b", to_datetime("9:15"), None),
        (
            [
                rowentry("a", "b", "9:00", "9:15"),
                rowentry("a", "b", "9:05", "9:10"),
            ],
            "a",
            "b",
            to_datetime("8:50"),
            to_datetime("9:10"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15"),
                rowentry("a", "b", "10:00", "10:15"),
                rowentry("a", "b", "11:00", "11:15"),
                rowentry("a", "b", "12:00", "12:15"),
            ],
            "a",
            "b",
            to_datetime("10:30"),
            to_datetime("11:15"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:10"),
                rowentry("d", "e", "9:00", "9:10"),
            ],
            "a",
            "d",
            to_datetime("9:00"),
            None,
        ),
    ],
)
def test_graph_connections(
    connections, start, end, departure_time, expected_arrival_time
):
    g = Graph(connections)
    assert g.get_arrival_time(start, end, departure_time) == expected_arrival_time


@pytest.mark.parametrize(
    "edges, node_to_remove, node_to_check, expected_neighbours",
    [
        # Test case 1: Remove node "a" and check neighbours of "b"
        ([rowentry("a", "b", "9:00", "9:15")], "a", "b", set()),
        # Test case 2: Remove node "b" and check neighbours of "a"
        ([rowentry("a", "b", "9:00", "9:15")], "b", "a", set()),
        # Test case 3: Remove node "b" and check neighbours of "a" with bidirectional edges
        (
            [
                rowentry("a", "b", "9:00", "9:15"),
                rowentry("b", "a", "9:00", "9:15"),
            ],
            "b",
            "a",
            set(),
        ),
    ],
)
def test_remove_node(edges, node_to_remove, node_to_check, expected_neighbours):
    g = Graph(edges)
    g.remove_node(node_to_remove)
    assert set(g.get_neighbouring_nodes(node_to_check)) == expected_neighbours


@pytest.mark.parametrize(
    "edges, start_node, end_node, bus_n, expected_weight",
    [
        ([rowentry("a", "b", "9:00", "9:15", "A")], "a", "b", "A", 0),
        ([rowentry("a", "b", "9:00", "9:15", "A")], "a", "b", "B", 1),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "A"),
                rowentry("c", "d", "9:00", "9:15", "A"),
            ],
            "a",
            "d",
            "B",
            None,
        ),
    ],
)
def test_bus_change_weight(edges, start_node, end_node, bus_n, expected_weight):
    g = Graph(edges)
    assert g.get_transfer_weight(start_node, end_node, bus_n) == expected_weight
