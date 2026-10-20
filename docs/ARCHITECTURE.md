# Pipeline Pulse: engineering notes

## Product decision

The product is an investigation workspace rather than an input/report landing page. Each view answers a distinct question; controls change the actual Python model. Synthetic presets provide reproducible demonstrations without claiming enterprise telemetry.

## Computation

The scheduler validates a DAG, runs ready tasks under a finite worker budget, advances a discrete event queue, retries bounded failures with capped exponential backoff, and propagates failure to dependent tasks. The healthy critical path is computed separately as a dependency lower bound.

## Runtime boundary

The public demo is static GitHub Pages with Pyodide 0.27.7. A worker loads `common.py`, `engine.py`, and `lab.py`; it receives a JSON request and returns a JSON-compatible result. All analysis is Python. DOM interaction and charts are JavaScript/SVG. Python startup has a 90-second timeout; each analysis has a 30-second timeout and a stop control. Terminating the worker releases the computation. Native CLI and API entry points use the same engine without WebAssembly.

## State and data

Inputs are editable and stay in the tab. Successful exports bind to the input submitted for that run, rather than a subsequently edited form. Experiment snapshots retain summary metrics in memory, with a maximum of four. Reload clears snapshots. There are no analytics, server uploads, external model calls, or automatic input persistence. Exporting an experiment includes its input and must be reviewed before sharing.

## Accessibility and display

Semantic buttons, form labels, visible focus, keyboard-accessible tabs, a skip link, reduced-motion support, and responsive layouts are included. Pipeline nodes can be selected with Enter/Space as well as pointer clicks. Narrow pipeline canvases scroll horizontally so activity labels remain readable. Charts are accompanied by evidence or textual summaries. Light themes preserve the portfolio's pearl/champagne direction.

## Tradeoffs and limitations

Retries occupy a worker during backoff. Each failed attempt consumes the configured activity duration. Scheduling is deterministic and uses input topological order as a tie-breaker. This is a synthetic digital twin, not an Azure connector or cloud execution engine.

## Validation

The repository tests both the original and advanced engine, serialization, algorithm boundaries, and invalid requests. `scripts/check_site.py` checks browser/native Python parity and deployable assets. Tests are run through GitHub Actions on every push. Browser interaction validation is recorded in the delivery notes rather than represented as automated end-to-end CI.

## First-visit preview

`sample-result.js` contains the native Python result for the synthetic studio sample, generated at build time. The UI labels it Synthetic preview until the visitor runs the worker. Exports and snapshots enable only after an actual Python run. This provides a useful first visit without pretending a browser computation has already happened.
