<p align="center"><a href="https://m-qazi99.github.io/pipeline-pulse/"><img src="docs/banner.svg" alt="Pipeline Pulse Studio — A pipeline graph that explains the cost of a failure." width="100%"></a></p>
<p align="center"><a href="https://m-qazi99.github.io/pipeline-pulse/"><strong>Launch the interactive studio ↗</strong></a> · <a href="#run-locally">Run Python locally</a> · <a href="docs/ARCHITECTURE.md">Architecture</a> · <a href="tests/test_studio.py">Tests</a></p>
<p align="center"><img src="https://github.com/m-qazi99/pipeline-pulse/actions/workflows/tests.yml/badge.svg" alt="Python engine checks"> <img src="https://img.shields.io/badge/Python-3.11%2B-477a62?style=flat-square" alt="Python 3.11+"> <img src="https://img.shields.io/badge/License-MIT-bb985b?style=flat-square" alt="MIT license"></p>

# Pipeline Pulse Studio

**A pipeline graph that explains the cost of a failure.**

An interactive failure laboratory for data pipelines. Shape a DAG, inject a fault, and watch the consequences propagate.

<p align="center"><a href="https://m-qazi99.github.io/pipeline-pulse/"><img src="docs/studio-preview.jpg" alt="pipeline-pulse studio running actual Python" width="100%"></a></p>

## Explore the product

Select **Cascade failure** → inspect `transform` → open **Recovery comparison** → compare completion coverage → replay the execution.

| Capability | What you can inspect |
|---|---|
| Discrete-event DAG scheduling | Python-computed results, accessible controls, and exportable evidence |
| Failure blast radius | Python-computed results, accessible controls, and exportable evidence |
| Interactive execution replay | Python-computed results, accessible controls, and exportable evidence |
| Critical path and recovery comparisons | Python-computed results, accessible controls, and exportable evidence |

The interface includes three synthetic scenarios, four workspace views, light multicolor themes, editable inputs, local file loading, in-memory experiment snapshots, keyboard shortcuts, and downloadable artifacts. The **input editor** exposes the real experiment rather than hiding the model behind a decorative dashboard.

## Python mechanics

The scheduler validates a DAG, runs ready tasks under a finite worker budget, advances a discrete event queue, retries bounded failures with capped exponential backoff, and propagates failure to dependent tasks. The healthy critical path is computed separately as a dependency lower bound.

## Run locally

No Python packages are required. Use Python 3.11 or newer.

```bash
git clone https://github.com/m-qazi99/pipeline-pulse.git
cd pipeline-pulse
python server.py
```

Open **http://127.0.0.1:8000**. The local server exposes the native Python API; the web UI uses the browser worker so its behavior matches the public demo. The public site requires a modern browser with WebAssembly and access to the runtime CDN.

```bash
# Native Python CLI: no browser, CDN, or third-party packages
python src/cli.py < examples/studio.json

# Native Python HTTP API
curl -s http://127.0.0.1:8000/api/analyze \
  -H 'Content-Type: application/json' \
  --data-binary @examples/studio.json

# Engine, boundary, and regression tests
python -m unittest discover -s tests -v
python scripts/check_site.py

# Regenerate the labeled synthetic first-visit preview
python scripts/build_preview.py
```

`examples/studio.json` is the complete version-2 experiment request. The `workspace: "studio"` field selects the advanced engine in `src/lab.py`. The original version-1 API remains available through `examples/sample.json` for compatibility. Errors return HTTP 400 with an `error` message; successful requests return metrics, evidence, artifacts, and a structured `lab` object for visualization.

## Architecture

```mermaid
flowchart TD
    I["Editable inputs and controls"] --> W["Background Python worker"]
    W --> E["engine.py → lab.py"]
    E --> V["Interactive investigation views"]
    E --> X["Evidence and artifacts"]
    A["Native CLI or local HTTP API"] --> E
```

- `src/lab.py` — the advanced, dependency-free Python computation.
- `src/engine.py` — explicit version routing and original API compatibility.
- `docs/lab.py`, `docs/engine.py`, `docs/common.py` — byte-identical browser copies, checked by CI.
- `docs/studio.js` — rendering, interaction, worker lifecycle; no duplicate analytical algorithm.
- `docs/worker.js` — pinned Pyodide 0.27.7 runtime in a Web Worker.
- `tests/` — **25 automated tests**, including scenario boundaries and regressions.
- `.github/workflows/tests.yml` — tests and browser/native source parity on each push.

## Scope and limitations

Retries occupy a worker during backoff. Each failed attempt consumes the configured activity duration. Scheduling is deterministic and uses input topological order as a tie-breaker. This is a synthetic digital twin, not an Azure connector or cloud execution engine.

Inputs remain in the active tab. Initial runtime files come from jsDelivr and fonts from Google Fonts; no input is sent to these services. Inputs and snapshots are not automatically persisted. Exported experiments include their input; review before sharing. File contents are limited to 2 MB and CSV datasets to 10,000 rows.

## Design and research

This studio is an independent implementation by **Muzammil Qazi**, developed with Codex assistance as a portfolio engineering project. Synthetic scenarios demonstrate the algorithms; they are not employer deliverables or evidence of production adoption. See [design decisions](docs/ARCHITECTURE.md) and [research references](docs/RESEARCH.md).

[Portfolio](https://m-qazi99.github.io/) · [GitHub](https://github.com/m-qazi99) · [MIT](LICENSE)
