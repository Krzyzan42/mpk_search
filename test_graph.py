from datetime import datetime

import pytest
from graph import ExpandedGraph, RowEntry, Node
from typing import Optional, Tuple

import graph


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
            (15, "9:15"),
        ),
        (
            [rowentry("a", "b", "9:00", "9:15", "101")],
            ("a", "101"),
            ("b", "101"),
            "8:45",
            (30, "9:15"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:05", "9:10", "101"),
            ],
            ("a", "101"),
            ("b", "101"),
            "9:00",
            (10, "9:10"),
        ),
        (
            [
                rowentry("a", "b", "9:00", "9:15", "101"),
                rowentry("a", "b", "9:05", "9:10", "101"),
            ],
            ("a", "101"),
            ("b", "101"),
            "10:00",
            (None, None),
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
            (5, "9:00"),
        ),
    ],
)
def test_time_weight(nodes, where_from, where_to, at, expected_result):
    graph = ExpandedGraph(nodes, transfer_cost=5)
    a = graph.get_node(where_from[0], where_from[1])
    b = graph.get_node(where_to[0], where_to[1])
    t = to_datetime(at)

    if not isinstance(expected_result, Tuple):
        with pytest.raises(expected_result):
            graph.get_connection_weight(a, b, t)
        return

    assert graph.get_connection_weight(a, b, t) == (
        expected_result[0],
        to_datetime(expected_result[1]),
    )


def test_remove_node():
    graph = ExpandedGraph([rowentry("a", "b", bus="101")])
    b_node = graph.get_node("b", "101")
    graph.remove_node(b_node)

    assert set(graph.get_nodes()) == set([Node("a", "101")])
    a_node = graph.get_node("a", "101")
    assert graph.get_neighbouring_nodes(a_node) == []

    with pytest.raises(ValueError):
        graph.get_connection_weight(a_node, b_node, to_datetime("9:90"))


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
        graph.get_connection_weight(a_101, a_102, to_datetime("9:90"))


def test_heuristics():
    graph = ExpandedGraph(
        [rowentry("a", "b", bus="101", a_coords=(99, 99), b_coords=(2, 2))],
        cost_per_kilometer=1,
        transfer_cost=0,
        cost_per_minute=0,
    )

    a_node = graph.get_node("a", "101")
    b_node = graph.get_node("b", "101")
    print(b_node.longitude)

    assert (
        graph.get_connection_weight(
            a_node,
            b_node,
            to_datetime("8:00"),
            heuristic_target=(2, 0),
        )[0]
        == 2
    )
