from __future__ import annotations

from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")
from pprint import pformat

import copy


class GraphNode:
    def __init__(self, name: str):
        self.name = name
        self.neighbors = []

    def __deepcopy__(self, memo: dict):
        logF.info(f"deepcopy : name = {self.name} = {id(self)} : {hex(id(self))}\n{pformat(memo)}")

        # Проверяем, не копировали ли этот объект ранее
        if id(self) in memo:
            return memo[id(self)]

        # Создаем новый объект и сохраняем в memo
        new_node = GraphNode(self.name)
        logF.info(f"memo append: {new_node.name} {id(self)} -> {hex(id(new_node))}")
        memo[id(self)] = new_node

        # Рекурсивно копируем соседей
        new_node.neighbors = [copy.deepcopy(n, memo) for n in self.neighbors]
        return new_node

    def add_neighbor(self, graph_node: GraphNode):
        self.neighbors.append(graph_node)


def deep_start():
    logF.info(f"'****' deep_start - 'start'")

    node1 = GraphNode("A")
    node2 = GraphNode("B")
    node3 = GraphNode("C")

    node1.add_neighbor(node2)
    node1.add_neighbor(node3)
    node2.add_neighbor(node1)

    node1_copy = copy.deepcopy(node1)

    logF.info(f"result = {node1_copy.neighbors[0].neighbors[0] is node1_copy}")  # True
