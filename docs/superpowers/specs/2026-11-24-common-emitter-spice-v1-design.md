# Common-Emitter Amplifier Simulator v1 — ngspice integration

**Date:** 2026-11-24
**Status:** Approved in conversation (integration plan + explicit approval message)

## Intent

Extend the existing ENG29 2121 Lab 3 Flask DC-bias app into a minimal Lab 4
Common-Emitter Amplifier Simulator v1. Keep the three analytical DC bias modes,
their results, and their 43 tests exactly as they are. Add real ngspice `.op`,
`.ac`, and `.tran` runs for **one** reference CE voltage-divider circuit, with
plots drawn only from values that ngspice actually produced.

An instructor-verified starter kit was searched for (repo, Desktop, Documents,
Downloads) and **not found**. The engine and netlist are therefore written
from the published Lab 4 brief and validated against a real ngspice-47 binary.

## Goals

- Preserve `POST /` analytical behaviour for all three bias modes.
- Add an analysis selector (`dc` / `ac` / `tran`) and amplitude/frequency inputs.
- Run ngspice as an external process with a list argument, no `shell=True`,
  an explicit timeout, and a per-run temp working directory.
- Show: DC table (VB, VE, VC, VCE, IC), AC gain/phase vs frequency, transient
  Vin/Vout vs time, with units, provenance labels, and the netlist used.
- Keep analytical numbers and SPICE numbers visibly separate.
- Expose every engine failure: bad exit code, `Error:` in output, timeout,
  missing/unparsable `.print` tables. Never substitute fabricated data.
- Document model, fixture values, comparison assumptions, and browser evidence.

## Non-goals

- Emitter bypass variants (`CE`), animated overlay, other bias modes under
  SPICE, drag-and-drop editor, FET/MOSFET, deploying publicly.
- Replacing or renaming `app.py`, `bjt_bias.py`, `bias_modes.py`,
  `independent_check.py`, or moving the project into `transistor-simulator/`.
- Changing the existing divider schematic for DC bias mode.

## Architecture

```
Browser form (analysis + amplitude/frequency)
        -> app.py: validate + dispatch
        -> spice_engine.py: netlist -> subprocess -> parse .print tables
        -> ngspice_con.exe (.op / .ac / .tran)
        -> matplotlib PNG (real arrays) + Jinja results
        -> docs/validation.md (comparison + browser log)
```

Lab 3 path stays on `bjt_bias.py` / `bias_modes.py` /
`independent_check.py`; SPICE path is additive.

## Decisions

### Reference circuit and fixture values

`VCC/R1/R2 = 12 V / 100 kΩ / 22 kΩ`, `RC/RE/RL = 2.2 kΩ / 1 kΩ / 10 kΩ`,
`Cin = Cout = 10 µF`, source `10 mV peak / 1 kHz` as defaults. Only amplitude
and frequency are editable in the form; capacitors/load are fixed, documented
constants shown in the netlist. No bypass capacitor in v1.

Nodes: `vcc`, `input` (source side of Cin), `base` (after Cin, divider midpoint),
`collect`, `emit`, `output` (after Cout, across RL). DC: capacitors open, so RL
is disconnected. AC gain reference is **V(output) / V(base)** — Vin is measured
at the base after Cin, declared on the page and in the docs. Transient Vin is
`v(input)` (source side), Vout is `v(output)`.

### BJT model

No instructor model was supplied, so the netlist states one explicitly and
reproducibly:

```
.model CEQ NPN(IS=1E-14 BF=<beta from form> VAF=100)
```

`BF` is the only link between the analytical β field and SPICE. The analytical
VBE field is **not** a SPICE parameter: SPICE derives VBE from IS/BF. IS and
VAF are fixed, documented constants. Analytical output remains an independent
rough reference (fixed VBE, constant β); values are not expected to match
digit-for-digit and the page says so.

### Engine contract (`spice_engine.py`)

- `build_netlist(analysis, values) -> str` — circuit + analysis line +
  `.print` lines. Uses long node names (single-letter nodes caused ngspice
  `.print` parse warnings during recon).
- `run(analysis, values) -> RunResult` — `subprocess.run([exe, "-b", netlist],
  timeout=..., cwd=tempdir, capture_output=True, text=True)`; returns netlist,
  stdout+stderr, return code, executable path.
- `parse_op/parse_ac/parse_tran(text) -> dict` — parse `Index ...` tables.
  AC phase from `vp()` is **radians** in this ngspice batch build and is
  converted to degrees in Python. Gain dB = `vdb(output) - vdb(base)`.
  Cutoff (-3 dB from midband maximum) is interpolated only when the sweep
  actually crosses it; otherwise the literal string
  `not determined in sweep range`.
- `SimulationError` carries a user-facing message plus the engine detail.
- Binary discovery: an explicit `NGSPICE_PATH` is authoritative (invalid value
  fails fast, no silent fallback); otherwise repo
  `tools/ngspice/Spice64/bin/ngspice_con.exe`, then PATH. `ngspice.exe` is
  unused (silent in this environment).

### Sweeps

AC: `dec 20 1 10Meg` (141 points) to cover coupling-capacitor corners.
Transient: `10 µs` step, `5 ms` stop (five 1 kHz periods), step shortened for
higher frequencies so at least ~20 points/period are kept; only real sample
rows are plotted.

### Plots

matplotlib (Agg) two- or three-panel figures rendered to PNG bytes and shown
as base64 data URIs, with axis labels/units. AC: gain (dB) and phase (deg) vs
frequency (Hz, log axis). Transient: Vin and Vout (V) vs time (ms). No plot is
created when parsing fails.

### Error paths

| Condition | User-visible result |
| --- | --- |
| ngspice binary missing | status Error with searched paths; no plot |
| amplitude/frequency invalid or non-positive | field error before netlist |
| exit code != 0 or `Error:`/`Fatal error` in output | Error status + excerpt; no plot |
| timeout | Error status with timeout value; no plot |
| `.print` table missing / empty / non-numeric | Error status with table name; no plot |
| no -3 dB crossing | `not determined in sweep range` text, real curve still shown |
| fixed/emitter bias + analysis selector | ignored; Lab 3 analytical result only |

Warnings such as `can't parse 'base': ignored` occur in successful ngspice runs
and are not treated as errors; `Error:` lines are.

## Verification

- Existing suite `Ran 43 tests ... OK` and new engine tests green.
- Real `.op`, `.ac`, `.tran` runs from the Flask test client and Browser,
  with netlist/log/status captured in `docs/validation.md`.
- Browser check of form units, graph axes, analytical-vs-SPICE labels, error
  banner, and local demo at `http://127.0.0.1:5000`.
- Commit and push after review.
