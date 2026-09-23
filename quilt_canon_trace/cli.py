"""CLI for quilt-canon-trace."""
import argparse
import json
import sys
from pathlib import Path

from .walker import CanonGraph, SubstrateWalker, CanonNode, build_graph_from_canon_loader


DEFAULT_OUT = Path.home() / ".cache" / "quilt-canon-trace" / "trace.json"


def _build_graph_from_canon():
    """Build a graph from canon loader (re-using canon-mcp's loader as canonical)."""
    sys.path.insert(0, "/workspace/repos/quilt-canon-mcp")
    sys.path.insert(0, "/workspace/repos/quilt-canon-graph")
    # Use graph module's loader
    return build_graph_from_canon_loader("quilt_canon_mcp.loader")


def cmd_walk(args):
    """Walk the canon graph from a starting piece."""
    graph = _build_graph_from_canon()

    # Resolve start node
    start = args.start
    if not start or start not in graph.nodes:
        # Pick a node with all 5 doctrines as default
        nodes_with_all = [n for n, c in graph.nodes.items() if len(c.doctrines_hit) >= 5]
        if nodes_with_all:
            start = nodes_with_all[0]
        else:
            start = list(graph.nodes.keys())[0]
        print(f"Using start node: {start}")

    # Optional witness log
    witness_log = None
    if args.witness:
        try:
            sys.path.insert(0, "/workspace/repos/quilt-canon-witness")
            from quilt_canon_witness.witness import WitnessLog
            witness_log = WitnessLog(path=Path(args.witness))
        except Exception as e:
            print(f"⚠ Witness log unavailable: {e}")

    walker = SubstrateWalker(graph, witness_log=witness_log, seed=args.seed)
    trace = walker.walk(start, steps=args.steps, mode=args.mode)
    out = Path(args.output) if args.output else DEFAULT_OUT
    walker.save_trace(out)

    print(f"✓ Walked {len(trace)} steps from {start}")
    print(f"  Visited {len(set(t['node'] for t in trace))} unique canons")
    print(f"  Trace → {out}")
    if witness_log:
        print(f"  Witnessed {len(trace)} steps → witness log")


def cmd_summary(args):
    """Show summary of an existing trace."""
    p = Path(args.trace)
    if not p.exists():
        print(f"No trace at {p}")
        return
    data = json.loads(p.read_text())
    print(json.dumps(data["summary"], indent=2))


def cmd_list_nodes(args):
    """List available canon nodes that can be used as walk starts."""
    graph = _build_graph_from_canon()
    if args.filter:
        nodes = [(n, c) for n, c in graph.nodes.items() if args.filter.lower() in c.title.lower()]
    else:
        nodes = list(graph.nodes.items())[:args.limit]
    for n, c in nodes:
        print(f"  {n:30s} {c.title} ({len(c.doctrines_hit)} doctrines)")


def cmd_stats(args):
    graph = _build_graph_from_canon()
    print(f"Canon graph: {len(graph.nodes)} nodes")
    n_edges = sum(len(e) for e in graph.edges.values()) // 2
    print(f"Edges: {n_edges}")
    avg_rels = (2 * n_edges) / max(1, len(graph.nodes))
    print(f"Avg degree: {avg_rels:.2f}")


def main():
    p = argparse.ArgumentParser(description="quilt-canon-trace — substrate walker trajectory generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_w = sub.add_parser("walk", help="Walk the canon graph")
    p_w.add_argument("--start", help="Starting canon piece (file stem)")
    p_w.add_argument("--steps", type=int, default=10)
    p_w.add_argument("--mode", choices=["weight", "greedy", "bfs"], default="weight")
    p_w.add_argument("--seed", type=int, help="Random seed (default: random)")
    p_w.add_argument("--output", help=f"Output file (default: {DEFAULT_OUT})")
    p_w.add_argument("--witness", help="Witness log path (optional)")
    p_w.set_defaults(func=cmd_walk)

    sub.add_parser("stats", help="Show graph statistics").set_defaults(func=cmd_stats)

    p_l = sub.add_parser("list-nodes", help="List canon nodes")
    p_l.add_argument("--filter", help="Filter by title substring")
    p_l.add_argument("--limit", type=int, default=20)
    p_l.set_defaults(func=cmd_list_nodes)

    p_s = sub.add_parser("summary", help="Summary of an existing trace")
    p_s.add_argument("--trace", default=str(DEFAULT_OUT))
    p_s.set_defaults(func=cmd_summary)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
