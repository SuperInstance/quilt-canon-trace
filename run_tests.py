"""Test runner for quilt-canon-trace (no pytest dep)."""
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, "/workspace/repos/quilt-canon-trace")

from quilt_canon_trace.canary import canary
from quilt_canon_trace.walker import CanonNode, CanonGraph, SubstrateWalker, build_graph_from_canon_loader

results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


def t_canary():
    assert canary() == "0x24a555471370b18d"


def t_graph_build():
    g = CanonGraph()
    g.add_node(CanonNode("a", "Alpha", ["cells_are_scars", "witness_log_is_prediction"]))
    g.add_node(CanonNode("b", "Beta", ["cells_are_scars"]))
    g.add_node(CanonNode("c", "Gamma", ["substrate_quantum"]))
    g.build_edges()
    assert "a" in g.edges
    assert "c" in g.edges
    assert g.adjacent("a", "b")
    assert not g.adjacent("a", "c")  # no shared doctrine
    assert g.edges["a"]["b"] == 1
    assert g.edges["b"]["a"] == 1


def t_neighbors():
    g = CanonGraph()
    g.add_node(CanonNode("a", "A", ["cells_are_scars"]))
    g.add_node(CanonNode("b", "B", ["cells_are_scars"]))
    g.add_node(CanonNode("c", "C", ["cells_are_scars"]))
    g.add_node(CanonNode("d", "D", ["substrate_quantum"]))  # different doctrine
    g.build_edges()
    nbrs = g.neighbors("a")
    assert len(nbrs) == 2
    weights = sorted([w for _, w in nbrs])
    assert weights == [1, 1]


def t_walker_walk():
    g = CanonGraph()
    # Build a chain: a - b - c - d
    g.add_node(CanonNode("a", "A", ["cells_are_scars", "witness_log_is_prediction"]))
    g.add_node(CanonNode("b", "B", ["cells_are_scars"]))
    g.add_node(CanonNode("c", "C", ["witness_log_is_prediction"]))
    g.add_node(CanonNode("d", "D", ["canon_gate_is_chord"]))
    g.build_edges()

    walker = SubstrateWalker(g, seed=42)
    trace = walker.walk("a", steps=3, mode="bfs")
    assert len(trace) == 4
    assert trace[0]["node"] == "a"
    assert trace[0]["via"] == "genesis"
    for t in trace[1:]:
        assert t["node"] in {"b", "c", "d"}


def t_walker_stuck():
    g = CanonGraph()
    # Isolated node
    g.add_node(CanonNode("solo", "Solo", ["cells_are_scars"]))
    g.build_edges()
    walker = SubstrateWalker(g, seed=42)
    trace = walker.walk("solo", steps=5)
    # Either stays at solo or restarts (no unvisited)
    assert trace[0]["node"] == "solo"


def t_walker_summary():
    g = CanonGraph()
    g.add_node(CanonNode("a", "A", ["cells_are_scars", "canon_gate_is_chord"]))
    g.add_node(CanonNode("b", "B", ["cells_are_scars"]))
    g.add_node(CanonNode("c", "C", ["witness_log_is_prediction"]))
    g.build_edges()
    walker = SubstrateWalker(g, seed=42)
    walker.walk("a", steps=2, mode="bfs")
    summary = walker.summary()
    # With 3 nodes and 2 steps, we have genesis + 2 = 3 trace records
    assert summary["n_steps"] >= 2
    assert "cells_are_scars" in summary["doctrine_coverage"]


def t_walker_save(tmp):
    g = CanonGraph()
    g.add_node(CanonNode("a", "A", ["cells_are_scars"]))
    g.add_node(CanonNode("b", "B", ["cells_are_scars"]))
    g.build_edges()
    walker = SubstrateWalker(g, seed=42)
    walker.walk("a", steps=1, mode="bfs")
    out = tmp / "trace.json"
    walker.save_trace(out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "trace" in data
    assert "summary" in data


def test_walker_with_witness(tmp):
    """Walker can append to witness log."""
    sys.path.insert(0, "/workspace/repos/quilt-canon-witness")
    from quilt_canon_witness.witness import WitnessLog

    g = CanonGraph()
    g.add_node(CanonNode("a", "A", ["cells_are_scars"]))
    g.add_node(CanonNode("b", "B", ["cells_are_scars"]))
    g.build_edges()

    log = WitnessLog(path=tmp / "w.jsonl")
    walker = SubstrateWalker(g, witness_log=log, seed=42)
    walker.walk("a", steps=2, mode="bfs")

    # Witness log should have records
    assert len(log.records) >= 1
    assert log.verify_chain()


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    test("test_canary", t_canary)
    test("test_graph_build", t_graph_build)
    test("test_neighbors", t_neighbors)
    test("test_walker_walk", t_walker_walk)
    test("test_walker_stuck", t_walker_stuck)
    test("test_walker_summary", t_walker_summary)
    test("test_walker_save_trace", lambda: t_walker_save(tmp))
    test("test_walker_with_witness", lambda: test_walker_with_witness(tmp))

print("\n=== quilt-canon-trace test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
