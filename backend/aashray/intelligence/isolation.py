from __future__ import annotations

import networkx as nx

from aashray.intelligence.data import load_graph


def build_graph(blocked_edge_ids: set[str]) -> nx.Graph:
    spec = load_graph()
    g = nx.Graph()
    for node in spec["nodes"]:
        g.add_node(node["id"], **node)
    for edge in spec["edges"]:
        if edge["id"] in blocked_edge_ids:
            continue
        g.add_edge(edge["u"], edge["v"], id=edge["id"], last_access=edge.get("last_access", False))
    return g


def reachable_from_hub(blocked_edge_ids: set[str]) -> set[str]:
    spec = load_graph()
    g = build_graph(blocked_edge_ids)
    hub = spec["hub"]
    if hub not in g:
        return set()
    return set(nx.bfs_tree(g, hub).nodes())


def isolated_settlements(blocked_edge_ids: set[str]) -> list[str]:
    spec = load_graph()
    reached = reachable_from_hub(blocked_edge_ids)
    names: list[str] = []
    for node in spec["nodes"]:
        settlement = node.get("settlement")
        if settlement and node["id"] not in reached:
            names.append(settlement)
    return names


def node_reachable(node_id: str, blocked_edge_ids: set[str]) -> bool:
    return node_id in reachable_from_hub(blocked_edge_ids)


def poi_reachable(poi_id: str, blocked_edge_ids: set[str]) -> bool:
    spec = load_graph()
    node = spec.get("poi_nodes", {}).get(poi_id)
    if not node:
        return True
    return node_reachable(node, blocked_edge_ids)


def last_access_blocked(blocked_edge_ids: set[str]) -> bool:
    spec = load_graph()
    return any(e.get("last_access") and e["id"] in blocked_edge_ids for e in spec["edges"])


def cascade_text() -> str:
    return load_graph().get("cascade", "Medical access delayed — last road blocked.")
