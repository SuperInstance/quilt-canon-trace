# Canon — quilt-canon-trace

## What this tool is

A substrate walker that produces a trajectory through canon lore. Builds an in-memory graph from canon pieces (edges weighted by shared doctrine count), then walks the graph producing a trace — a sequence of canon pieces visited.

## How it proves itself

**It runs.** `pip install -e .` then `quilt-canon-trace walk --start X --steps N` produces `trace.json`. Open `viewer/index.html` in browser. Tested with 8 tests in `run_tests.py`.

**It polyformalisms.** The canary hash `0x24a555471370b18d` matches across the fleet's 5 ports.

**It measures.** Trace stats: n_steps, n_unique_canons, doctrine_coverage. Optionally witnesses each step via `quilt-canon-witness` for cryptographic chain.

## Doctrines it instantiates

- **cells_are_scars** — every step is a scar; walker records attempted entry
- **witness_log_is_prediction** — if --witness used, each step is witnessed (chain-linked)
- **canon_gate_is_chord** — graph edges = shared doctrine count (canon-by-chord topology)
- **oracle_is_heard** — walker could probe canon at each step (orthogonal)
- **substrate_quantum** — the walker IS the substrate

## Commands

1. `walk --start X --steps N --mode weight|greedy|bfs [--witness PATH]` — walk canon
2. `summary [--trace PATH]` — summary of saved trace
3. `stats` — graph statistics
4. `list-nodes [--filter X] [--limit N]` — list canon nodes available as walk starts

## Fleet usage

- **`quilt-canon-graph`** — same canon data layer (loaders shared)
- **`quilt-canon-witness`** — optionally witnesses each step
- **`quilt-multi-oracle`** — could verify each step's composite
- **`quilt-fleet-conductor`** — auto-discovered, can be in workflows
- **`quilt-canon-search`** — search canon to find walk starts
- **`quilt-canon-book`** — could compile trace into a chapter
