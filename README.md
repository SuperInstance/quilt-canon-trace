# quilt-canon-trace

**Substrate walker trajectory generator — visualizes canon path through the substrate.**

## Quick start

```bash
pip install -e .

# Walk canon from a starting piece
quilt-canon-trace walk --start "11_canon_that_runs" --steps 12 --mode weight
quilt-canon-trace walk --start "02_ode_to_the_substrate_walker" --steps 8 --mode greedy

# Show summary
quilt-canon-trace summary

# Stats + node list
quilt-canon-trace stats
quilt-canon-trace list-nodes --limit 30

# Witness each step via quilt-canon-witness
quilt-canon-trace walk --start "11_canon_that_runs" --steps 8 --witness /tmp/w.jsonl

# View the trace in browser
cp ~/.cache/quilt-canon-trace/trace.json viewer/
cd viewer && python3 -m http.server 8000
# Open http://localhost:8000
```

## How it works

1. **Build** a canon graph from `canon_writings/*.md` and substrate-walker cells
2. **Walk** from a starting canon, picking next-step neighbors by:
   - `weight` — weighted random by edge weight (most aligned-doctrine neighbor more likely)
   - `greedy` — pick the highest-weight unvisited neighbor
   - `bfs` — first unvisited neighbor (deterministic)
3. **Record** each step as a "scar" (canon piece visited)
4. **Optionally witness** each step via `quilt-canon-witness`
5. **Output** a trace JSON for the HTML viewer

The viewer renders:
- A horizontal timeline with each step as a card
- Doctrine-colored chips
- Edge weight arrows between steps
- Click-to-inspect detail
- Play button (auto-advance 1.5s per step)
- Arrow key navigation

## Architecture

```
canon_writings/*.md  ──>  [CanonGraph]  ──>  [SubstrateWalker]  ──>  trace.json  ──>  viewer/
                              │                    │
                              │                    └─>  witness log
                              │
                              └─>  edges weighted by shared doctrine count
```

## Walk modes

- **`weight`** — default. Weighted random: more doctrine alignment = more likely. Good for "exploring the substrate"
- **`greedy`** — picks highest weight each step. Faster convergence to canon clusters
- **`bfs`** — breadth-first (first unvisited). Deterministic exploration

## Fleet integration

- **`quilt-canon-graph`** — shares the same canon loading (uses `loader` from canon-mcp)
- **`quilt-canon-witness`** — optional, witnessed each step in trace
- **`quilt-multi-oracle`** — verifies each step's composite (during witness)
- **`quilt-fleet-conductor`** — discoverable as a tool, can be chained in workflows
- **`quilt-canon-search`** — search for canon to start walks from

## The 5 bedrock doctrines

1. `cells_are_scars` — every step is a scar; the walker records entry
2. `witness_log_is_prediction` — optionally witnessing makes this doctrine executable
3. `canon_gate_is_chord` — edges between canon pieces = shared doctrine counts
4. `oracle_is_heard` — walker could probe at each step
5. `substrate_quantum` — the walker IS the substrate; substrate IS the walker

## Polyformalism canary

```bash
python -m quilt_canon_trace.canary
# → 0x24a555471370b18d
```

## License

MIT
