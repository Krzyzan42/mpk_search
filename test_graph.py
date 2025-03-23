from datetime import datetime

import pytest
from graph import Connection, ExpandedGraph, RowEntry, Node
from typing import Tuple


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


def node(bus_stop, bus_n) -> Node:
    return Node(bus_stop, bus_n, 0, 0)


def test_creating_nodes():
    graph = ExpandedGraph(
        [
            rowentry("a", "b", bus="101"),
            rowentry("b", "c", bus="101"),
            rowentry("c", "b", bus="101"),
            rowentry("b", "a", bus="101"),
            rowentry("a", "b", bus="102"),
            rowentry("b", "d", bus="102"),
            rowentry("x", "y", bus="102"),
        ]
    )

    nodes = graph.get_nodes()
    expected = [
        node("a", "101"),
        node("b", "101"),
        node("c", "101"),
        node("a", "102"),
        node("b", "102"),
        node("d", "102"),
        node("x", "102"),
        node("y", "102"),
    ]
    assert set(nodes) == set(expected)


@pytest.mark.parametrize(
    "nodes, bus_stop, bus_n, expected",
    [
        ([rowentry("a", "b", bus="101")], "a", "101", [node("b", "101")]),
        ([rowentry("a", "b", bus="101")], "b", "101", []),
        (
            [rowentry("a", "b", bus="101"), rowentry("a", "c", bus="101")],
            "a",
            "101",
            [node("b", "101"), node("c", "101")],
        ),
        (
            [rowentry("a", "b", bus="101"), rowentry("a", "b", bus="102")],
            "a",
            "101",
            [node("b", "101"), node("a", "102")],
        ),
    ],
)
def test_neighboring_nodes(nodes, bus_stop, bus_n, expected):
    graph = ExpandedGraph(nodes)
    tested_node = graph.get_node(bus_stop, bus_n)
    assert set(graph.get_neighbouring_nodes(tested_node)) == set(expected)


@pytest.mark.parametrize(
    "nodes, where_from, where_to, at, expected_result",
    [
        (
            [rowentry("a", "b", "9:00", "9:15", "101")],
            ("a", "101"),
            ("b", "101"),
            "9:00",
            Connection(to_datetime("9:00"), to_datetime("09:15"), "101"),
        ),
        (
            [rowentry("a", "b", "9:00", "9:15", "101")],
            ("a", "101"),
            ("b", "101"),
            "8:45",
            Connection(to_datetime("9:00"), to_datetime("09:15"), "101"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:05", "9:10", "101"),
            ],
            ("a", "101"),
            ("b", "101"),
            "9:00",
            Connection(to_datetime("9:05"), to_datetime("09:10"), "101"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:05", "9:10", "101"),
            ],
            ("a", "101"),
            ("b", "101"),
            "10:00",
            None
        ),
        (
            [rowentry("a", "b", "9:00", "9:15", "101")],
            ("b", "101"),
            ("a", "101"),
            "9:00",
            ValueError,
        ),
        (
            [rowentry("a", "b", "9:00", "9:15", "101")],
            ("b", "101"),
            ("a", "101"),
            "9:00",
            ValueError,
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:00", "9:15", "102"),
            ],
            ("a", "101"),
            ("a", "102"),
            "9:00",
            ValueError
        ),
    ],
)
def test_time_weight(nodes, where_from, where_to, at, expected_result):
    graph = ExpandedGraph(nodes)
    a = graph.get_node(where_from[0], where_from[1])
    b = graph.get_node(where_to[0], where_to[1])
    t = to_datetime(at)

    if isinstance(expected_result, type):
        with pytest.raises(expected_result):
            graph.get_best_connection(a, b, t)
        return

    assert graph.get_best_connection(a, b, t) == expected_result


def test_remove_node():
    graph = ExpandedGraph([rowentry("a", "b", bus="101")])
    b_node = graph.get_node("b", "101")
    graph.remove_node(b_node)

    assert set(graph.get_nodes()) == set([Node("a", "101")])
    a_node = graph.get_node("a", "101")
    assert graph.get_neighbouring_nodes(a_node) == []

    with pytest.raises(ValueError):
        graph.get_best_connection(a_node, b_node, to_datetime("9:90"))


def test_remove_node__same_bus_line():
    graph = ExpandedGraph(
        [rowentry("a", "b", bus="101"), rowentry("a", "c", bus="102")]
    )
    a_101 = graph.get_node("a", "101")
    graph.remove_node(a_101)

    assert set(graph.get_nodes()) == set(
        [Node("a", "102"), Node("b", "101"), Node("c", "102")]
    )
    a_102 = graph.get_node("a", "102")
    assert graph.get_neighbouring_nodes(a_102) == [Node("c", "102")]

    with pytest.raises(ValueError):
        graph.get_best_connection(a_101, a_102, to_datetime("9:90"))


