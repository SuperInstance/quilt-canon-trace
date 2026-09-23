"""Substrate walker — generates a trajectory through canon lore.

The walker:
- Starts at a canon piece (a cell)
- Picks its next cell based on shared doctrines (graph edge weight)
- Each step is a "scar" (cell that records attempted entry)
- Optionally witnesses each step via quilt-canon-witness
- Outputs a trace (sequence of canon piece IDs)

This is the substrate walker as a substance: it walks canon.
"""
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CanonNode:
    """A single canon piece in the substrate."""
    def __init__(self, name: str, title: str, doctrines_hit: List[str], body: str = ""):
        self.name = name
        self.title = title
        self.doctrines_hit = doctrines_hit
        self.body = body

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "doctrines_hit": self.doctrines_hit,
            "body_preview": self.body[:200],
        }


class CanonGraph:
    """In-memory canon graph: nodes + edges weighted by shared doctrines."""
    def __init__(self):
        self.nodes: Dict[str, CanonNode] = {}
        self.edges: Dict[str, Dict[str, float]] = defaultdict(dict)  # adjacency

    def add_node(self, node: CanonNode):
        self.nodes[node.name] = node

    def build_edges(self):
        """Build edges by pairwise shared doctrines (weight = doctrine count)."""
        # Ensure every node has an entry in edges (empty dict for isolated nodes)
        for n in self.nodes:
            self.edges[n]  # defaultdict access creates empty dict
        names = list(self.nodes.keys())
        for i, n1 in enumerate(names):
            for n2 in names[i + 1:]:
                p1 = self.nodes[n1]
                p2 = self.nodes[n2]
                shared = set(p1.doctrines_hit) & set(p2.doctrines_hit)
                if shared:
                    w = len(shared)
                    self.edges[n1][n2] = w
                    self.edges[n2][n1] = w

    def neighbors(self, node_name: str) -> List[Tuple[str, float]]:
        """Return (neighbor_name, weight) pairs for a node."""
        return [(n, w) for n, w in self.edges.get(node_name, {}).items()]

    def adjacent(self, a: str, b: str) -> bool:
        return b in self.edges.get(a, {})


class SubstrateWalker:
    """Walks the canon graph, optionally witnessing each scar."""

    def __init__(self, graph: CanonGraph, witness_log=None, seed: Optional[int] = None):
        self.graph = graph
        self.witness_log = witness_log
        if seed is not None:
            random.seed(seed)
        self.trace: List[Dict] = []
        self.visited: set = set()

    def step(self, current: str, mode: str = "weight") -> Optional[str]:
        """Take one step from current node. Returns the next node, or None if stuck."""
        neighbors = self.graph.neighbors(current)
        # Filter out visited
        neighbors = [(n, w) for n, w in neighbors if n not in self.visited]
        if not neighbors:
            return None

        if mode == "weight":
            # Weighted random by edge weight (stronger doctrine alignment = more likely)
            names = [n for n, _ in neighbors]
            weights = [w for _, w in neighbors]
            chosen = random.choices(names, weights=weights, k=1)[0]
        elif mode == "greedy":
            # Pick highest-weight unvisited neighbor
            neighbors.sort(key=lambda x: -x[1])
            chosen = neighbors[0][0]
        elif mode == "bfs":
            # First neighbor (deterministic)
            chosen = neighbors[0][0]
        else:
            chosen = neighbors[0][0]

        self.visited.add(chosen)
        return chosen

    def walk(self, start: str, steps: int = 10, mode: str = "weight") -> List[Dict]:
        """Walk the canon from start for steps iterations. Returns the trace."""
        if start not in self.graph.nodes:
            raise ValueError(f"Start node not in graph: {start}")

        self.trace = []
        self.visited = {start}

        current = start
        node = self.graph.nodes[current]
        rec = {
            "step": 0,
            "node": current,
            "title": node.title,
            "doctrines": node.doctrines_hit,
            "via": "genesis",
            "edge_weight": None,
        }
        self.trace.append(rec)

        if self.witness_log:
            self.witness_log.append(
                lore_ref=current,
                lore_text=node.body or node.title,
                probe_composite=1.0,
                doctrines_hit=node.doctrines_hit,
                agent="substrate-walker",
                note=f"trace step 0 (genesis): {node.title}"
            )

        for i in range(1, steps + 1):
            next_name = self.step(current, mode=mode)
            if next_name is None:
                # Stuck — pick any unvisited node as restart
                unvisited = [n for n in self.graph.nodes if n not in self.visited]
                if not unvisited:
                    break
                next_name = random.choice(unvisited)
                self.visited.add(next_name)
                via = "restart"
                edge_weight = 0
            else:
                via = "step"
                edge_weight = self.graph.edges[current][next_name]

            current = next_name
            node = self.graph.nodes[current]

            rec = {
                "step": i,
                "node": current,
                "title": node.title,
                "doctrines": node.doctrines_hit,
                "via": via,
                "edge_weight": edge_weight,
            }
            self.trace.append(rec)

            if self.witness_log:
                self.witness_log.append(
                    lore_ref=current,
                    lore_text=node.body or node.title,
                    probe_composite=edge_weight / 5.0,  # normalize
                    doctrines_hit=node.doctrines_hit,
                    agent="substrate-walker",
                    note=f"trace step {i}: {node.title} (via {via}, weight {edge_weight})"
                )

        return self.trace

    def summary(self) -> Dict:
        """Summary of the trace."""
        if not self.trace:
            return {"n_steps": 0}
        doctrine_visits = defaultdict(int)
        for t in self.trace:
            for d in t.get("doctrines", []):
                doctrine_visits[d] += 1
        return {
            "n_steps": len(self.trace),
            "n_unique_canons": len(set(t["node"] for t in self.trace)),
            "doctrine_coverage": dict(doctrine_visits),
            "visited_count": len(self.visited),
            "started_at": self.trace[0]["node"],
            "ended_at": self.trace[-1]["node"],
        }

    def save_trace(self, path: Path):
        """Save the trace as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "summary": self.summary(),
            "trace": self.trace,
        }, indent=1))


def build_graph_from_canon_loader(loader_module, exclude_names: Optional[List[str]] = None) -> CanonGraph:
    """Build a CanonGraph from the canon loader module."""
    from importlib import import_module
    loader = import_module(loader_module)
    pieces = loader.load_canon()
    if exclude_names:
        pieces = [p for p in pieces if not any(en in p.name for en in exclude_names)]

    g = CanonGraph()
    for p in pieces:
        g.add_node(CanonNode(
            name=p.name,
            title=p.title,
            doctrines_hit=p.doctrines_hit,
            body=p.body or "",
        ))
    g.build_edges()
    return g
