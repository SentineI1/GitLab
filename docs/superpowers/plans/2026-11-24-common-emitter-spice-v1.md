# Common-Emitter Amplifier Simulator v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real ngspice `.op`/`.ac`/`.tran` runs and data-driven plots for one CE voltage-divider circuit without touching the three Lab 3 analytical DC modes.

**Architecture:** `app.py` keeps owning HTTP validation/dispatch; new `spice_engine.py` owns netlist → external process → `.print` table parsing; new `plots.py` renders parsed arrays to PNG. Jinja template extends the existing page with an analysis selector, amplitude/frequency fields, provenance labels and graphs.

**Tech Stack:** Python 3.12, Flask 3, ngspice-47 console binary, matplotlib (Agg), unittest.

**Spec:** `docs/superpowers/specs/2026-11-24-common-emitter-spice-v1-design.md`

## Global Constraints

- Keep `app.py`, `bjt_bias.py`, `bias_modes.py`, `independent_check.py` behaviour and the existing 43 tests intact; no rename, no new subdirectory.
- No instructor starter kit exists in this environment; model is `.model CEQ NPN(IS=1E-14 BF=<beta> VAF=100)` with BF from the form; IS/VAF fixed and documented.
- Engine binary is `tools/ngspice/Spice64/bin/ngspice_con.exe` (gitignored); overridable with `NGSPICE_PATH`; never use `ngspice.exe` here.
- `subprocess.run([exe, "-b", netlist], timeout=20, cwd=<tempdir>, capture_output=True, text=True)`; never `shell=True`.
- Reference circuit: VCC/R1/R2 = 12 V/100 kΩ/22 kΩ, RC/RE/RL = 2.2 kΩ/1 kΩ/10 kΩ, Cin=Cout=10 µF, 10 mV peak/1 kHz defaults; no bypass capacitor.
- AC gain reference is `v(output)/v(base)`; `vp()` values in batch output are radians and must be converted to degrees.
- Never fabricate data, hard-code success values, or hide ngspice errors; no plot when parsing fails.
- Cutoff label when absent: literal `not determined in sweep range`.
- Fixed/emitter bias modes remain analytical-only.

## Review Focus

1. **amplitude or frequency = 0 / negative / non-numeric** → field error before any netlist is built; pinned in Task 2 Step 1.
2. **ngspice missing (`NGSPICE_PATH` points nowhere)** → Error status listing searched paths, no plot; pinned in Task 1 Step 1.
3. **exit code 0 but output contains `Error:`** → treated as failure; pinned in Task 1 Step 1 (`check_run`).
4. **sweep with no −3 dB crossing** → `not determined in sweep range`, real curve still plotted; pinned in Task 1 Step 1 (`cutoff_frequencies`).
5. **analytical and SPICE numbers shown together** → each block labelled with its source and assumptions; pinned in Task 2 Step 1.

---

### Task 1: `spice_engine.py` — netlist, process, parsers

**Files:**
- Create: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: `values` mapping with keys `vcc, r1, r2, rc, re, beta, amplitude_mv, frequency_hz` (SI floats, from `bias_modes.parse_for_mode` plus validated source fields).
- Produces:
  - `SimulationError(message: str, detail: str = "")`
  - `RunResult(analysis: str, netlist: str, stdout: str, returncode: int, exe: str)`
  - `resolve_ngspice() -> str`, `check_run(result: RunResult) -> None`
  - `build_netlist(analysis: str, values: Mapping[str, float]) -> str`
  - `run(analysis: str, values: Mapping[str, float], exe: str | None = None, timeout: int = 20) -> RunResult`
  - `parse_op(text: str) -> dict`, `parse_ac(text: str) -> dict`, `parse_tran(text: str) -> dict`
  - `cutoff_frequencies(frequencies: Sequence[float], gain_db: Sequence[float]) -> tuple[float | None, float | None]`
  - `simulate(analysis: str, values: Mapping[str, float], exe: str | None = None, timeout: int = 20) -> dict`

- [ ] **Step 1: Write failing tests for netlist, error gates, parsers and a real run**

Create `tests/test_spice_engine.py` with:

```python
VALUES = {"vcc": 12.0, "r1": 100_000.0, "r2": 22_000.0, "rc": 2_200.0,
          "re": 1_000.0, "beta": 150.0, "amplitude_mv": 10.0, "frequency_hz": 1_000.0}

def test_netlist_has_model_and_analysis():
    nl = build_netlist("ac", VALUES)
    assert ".model CEQ NPN(IS=1E-14 BF=150 VAF=100)" in nl
    assert ".ac dec 20 1 10Meg" in nl
    assert "Cin input base 10u" in nl and "Cout collect output 10u" in nl
    assert "RL output 0 10k" in nl
    assert "Vs input 0 DC 0 AC 0.01 SIN(0 0.01 1000)" in nl
    assert ".print ac vdb(output)" in nl and ".print ac vp(base)" in nl

def test_op_and_tran_analysis_lines():
    assert ".op" in build_netlist("dc", VALUES)
    assert ".tran 10u 5m 0 10u" in build_netlist("tran", VALUES)

def test_check_run_rejects_error_text_with_zero_exit():
    r = RunResult("dc", "", "Error: no data saved", 0, "fake")
    with self.assertRaises(SimulationError):
        check_run(r)

def test_resolve_ngspice_reports_bad_env():
    with patch.dict(os.environ, {"NGSPICE_PATH": r"C:\does\not\exist\ngspice.exe"}):
        with self.assertRaises(SimulationError) as cm:
            resolve_ngspice()
    self.assertIn("does\\not\\exist", str(cm.exception))

def test_parse_op_reads_ngspice_table():
    text = ("Index   v(base)         v(emit)         v(collect)      @q1[ic]\n"
            "--------------------------------------------------------------------------------\n"
            "0\t2.013016e+00\t1.352006e+00\t9.044000e+00\t1.344126e-03\n")
    d = parse_op(text)
    assert abs(d["vb_v"] - 2.013016) < 1e-6
    assert abs(d["ic_ma"] - 1.344126) < 1e-6
    assert abs(d["vce_v"] - (9.044 - 1.352006)) < 1e-6

def test_parse_ac_and_cutoff_reports_missing_crossing():
    text = four fake tables like the real ones, each with header containing
    'vdb(output)', 'vp(output)', 'vdb(base)', 'vp(base)' and 3 rows
    f = [10.0, 1000.0, 100000.0]
    # phase values are radians: vp(output) ~ pi less than vp(base)
    d = parse_ac(text)
    assert len(d["frequency_hz"]) == 3
    assert abs(d["gain_db"][1] - 4.895) < 0.3
    assert abs(d["phase_deg"][1] + 180) < 20
    assert cutoff_frequencies(f, [1.0, 1.0, 1.0]) == (None, None)

def test_parse_tran_reads_real_sample_count():
    text = header 'Index time v(input) v(output)' plus 3 numeric rows
    d = parse_tran(text)
    assert d["time_s"][0] == 0.0 and len(d["vin_v"]) == 3

def test_real_ngspice_smoke():
    skip unless resolve_ngspice() succeeds
    for analysis in ("dc", "ac", "tran"):
        result = simulate(analysis, VALUES)
        assert result["status"] == "success"
        assert result["netlist"] and result["log"]
        assert len(result["data"]["..."]) > 0   # analysis-specific array
```

Use `unittest` (`patch.dict(os.environ, ...)`, `@unittest.skipUnless`) to match
the existing test suite; `assertRaises` is `self.assertRaises`.

- [ ] **Step 2: Run the new tests to confirm they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_spice_engine -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'spice_engine'`.

- [ ] **Step 3: Implement `spice_engine.py`**

- `FIXTURE` constants: `CIN="10u"`, `COUT="10u"`, `RL="10k"`, model string;
  `_num()` formats floats with `:g`.
- `build_netlist`: nodes `vcc, input, base, collect, emit, output`; source line
  uses amplitude/1000 for both `AC` and `SIN(0 A F)`; `.ac dec 20 1 10Meg`;
  `.tran <step> 5m 0 <step>` where step is `10u` at ≤1 kHz, otherwise
  `f"{max(1e-9, 1/(frequency_hz*20)):g}"`; DC/AC/TRAN emit the exact `.print`
  lines from Step 1 (four separate AC prints, phase from `vp()` in radians).
- `run`: write netlist to `tempfile.TemporaryDirectory()`, call the list-form
  subprocess, return `RunResult` with combined stdout+stderr; propagate
  `TimeoutExpired`/`OSError` as `SimulationError` with detail.
- `check_run`: raise on nonzero return or regex `(?im)^\s*(?:error|fatal error):`
  or `run simulation\(s\) aborted`; include a 1500-character log excerpt in
  `SimulationError.detail`. Harmless `Warning: can't parse ...: ignored` lines
  must not fail.
- `parse_table(text, marker)`: find the `Index` header containing `marker`,
  then parse tab/space separated numeric rows until a non-numeric line.
  `parse_op/ac/tran` call it; missing/empty table raises `SimulationError`
  naming the marker.
- `parse_ac`: gain = `vdb(output)-vdb(base)`; phase =
  `(vp(output)-vp(base))*180/pi`, normalized to `(-180, 180]`;
  `midband_gain_db = max(gain_db)`; `cutoff_frequencies` interpolates the
  low/high crossings of `midband-3 dB` in log-frequency and returns
  `(None, None)` when absent. `simulate` converts `None` to
  `not determined in sweep range` in the result dict.
- `simulate`: build → run → check → parse → return
  `{"status":"success","analysis":...,"netlist":...,"log":...,"model":...,"data":...}`.
- `resolve_ngspice`: an explicit `NGSPICE_PATH` is authoritative — if set and
  not executable, raise `SimulationError` naming it (fail fast, no silent
  fallback). Otherwise try the repo binary, then PATH candidates; raise with
  all attempted paths when none is executable.

- [ ] **Step 4: Run the tests until green**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_spice_engine -v`
Expected: all new tests PASS, including three real ngspice runs.

- [ ] **Step 5: Commit**

```powershell
git add spice_engine.py tests/test_spice_engine.py
git commit -m "feat: add ngspice netlist, run and parse adapter"
```

---

### Task 2: Flask dispatch, source validation, plots and UI

**Files:**
- Modify: `app.py:22-52`, `app.py:55-94`, `templates/index.html`, `static/style.css`, `requirements.txt`, `tests/test_app.py`
- Create: `plots.py`

**Interfaces:**
- Consumes: `simulate()` and `SimulationError` from Task 1; existing
  `parse_for_mode`, `solve`, `MODE_LABELS`, `BiasInputError`.
- Produces:
  - `POST /` with `action=simulate`, `mode=divider`, `analysis in {dc,ac,tran}`
    renders `sim` (dict from `simulate`, or error dict with `status="error"`),
    `analysis`, `plot_ac`, `plot_tran`, plus the existing `result` labelled as
    analytical reference.
  - `plots.ac_plot(data) -> str` and `plots.tran_plot(data) -> str` return
    `data:image/png;base64,...` strings.
  - Other POSTs keep the exact Lab 3 context and output.

- [ ] **Step 1: Write failing Flask tests**

Add to `tests/test_app.py` (keep all existing tests untouched):

```python
DIVIDER = {**DEFAULTS, "r1": "100000", "r2": "22000", "rc": "2200",
           "amplitude_mv": "10", "frequency_hz": "1000"}
FIXED = {**DEFAULTS, "mode": "fixed"}

def test_simulate_dc_shows_spice_and_analytical_labels():
    r = self.client.post("/", data={**DIVIDER, "action": "simulate", "analysis": "dc"})
    self.assertIn(b"SPICE", r.data)
    self.assertIn(b"ngspice", r.data)
    self.assertIn(b"Analytical reference", r.data)
    self.assertIn(b".model CEQ NPN", r.data)

def test_simulate_rejects_zero_amplitude():
    r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                    "analysis": "tran", "amplitude_mv": "0"})
    self.assertIn(b"Amplitude", r.data)
    self.assertNotIn(b"Simulation complete", r.data)

def test_simulate_ac_renders_real_plot_data_uri():
    r = self.client.post("/", data={**DIVIDER, "action": "simulate", "analysis": "ac"})
    body = r.get_data(as_text=True)
    self.assertIn("data:image/png;base64,", body)
    self.assertIn("Frequency (Hz)", body)

def test_fixed_mode_ignores_simulate_action():
    r = self.client.post("/", data={**FIXED, "action": "simulate", "analysis": "ac"})
    self.assertIn(b"Fixed bias", r.data)
    self.assertNotIn(b"SPICE output", r.data)
```

- [ ] **Step 2: Run the new tests to confirm they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: the four new tests FAIL (no `sim` context / no labels).

- [ ] **Step 3: Extend `app.py`**

Add `amplitude_mv: "10"`, `frequency_hz: "1"` to `DEFAULTS`; extend
`ALL_FIELDS`; add `SIM_ANALYSES = ("dc", "ac", "tran")`. In `index()`, when
`action == "simulate"` and `mode == "divider"`: parse divider fields with the
existing `parse_for_mode`, validate amplitude (mV, > 0) and frequency (Hz or
kHz via suffix? **Hz only**, > 0, ≤ 1e9) with a small `_parse_sim_fields`
helper that raises `BiasInputError`; convert to volts; call `simulate()`;
catch `SimulationError` into `{"status":"error", ...}`; compute the same
analytical `result`/`independent`/`comparison` as today and render all of it
with `sim`, `analysis`, and plots. Other paths return exactly today's context.

- [ ] **Step 4: Add `plots.py` and install matplotlib**

Run `.\.venv\Scripts\python.exe -m pip install matplotlib`, add
`matplotlib>=3.8` to `requirements.txt`. In `plots.py` set Agg before pyplot
import, close every figure, and render:
- `ac_plot`: two stacked axes — gain dB vs frequency (log x) and phase deg vs
  frequency (log x); vertical markers only at real crossings.
- `tran_plot`: time (ms) vs Vin and Vout (V), first ~5 periods of real samples.
- axis titles include units; legends read `ngspice: ...`.
Return base64 data URI; on exception return `None` (the SPICE table still
shows, with an explicit "plot unavailable" note in the template).

- [ ] **Step 5: Extend `templates/index.html` and `static/style.css`**

In the form: analysis `<select name="analysis">` (DC / AC / Transient),
`amplitude_mv` (mV peak) and `frequency_hz` (Hz) inputs, and a second submit
`name="action" value="simulate"` labelled "Run Simulation". Keep the original
"Calculate" button unchanged. After the existing results table add a
`{% if sim %}` section: status badge (`success`/`error`), error detail `<pre>`
when present, `<details>` with the netlist and log excerpt, source-labelled
tables (`SPICE output — ngspice, model CEQ` vs `Analytical reference — fixed
beta/VBE`), cutoff text (`sim.data.f_low_hz`, `f_high_hz`), and
`{% if plot_ac %}<img...>{% endif %}` / `plot_tran`. Change the analytical
heading only when `sim` is set so the two are never mistaken for one dataset.
Add modest CSS for the simulation panel and plot sizing; no JS needed.

- [ ] **Step 6: Run all tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`
Expected: 43 existing + new engine/app tests all PASS.

- [ ] **Step 7: Commit**

```powershell
git add app.py plots.py templates/index.html static/style.css requirements.txt tests/test_app.py
git commit -m "feat: run and plot CE SPICE analyses in the web app"
```

---

### Task 3: Documentation, real browser verification and evidence

**Files:**
- Create: `AGENTS.md`, `docs/validation.md`, optional `docs/captures/`
- Modify: `README.md`

**Interfaces:**
- Consumes: running app from Task 2 and real `simulate()` output.
- Produces: reproducible setup instructions, provenance rules, validation table
  with **actual** ngspice numbers and browser log.

- [ ] **Step 1: Capture real engine evidence**

Run each analysis through the Flask test client (or live app) with the baseline
fixture and record in `docs/validation.md`: model line, sweep/stop commands,
return code, VB/VE/VC/VCE/IC, midband gain, phase, cutoff labels, log excerpt
location. Copy the analytical divider numbers from the existing path beside
them with the assumption note from the spec. No number may be written before
the run has produced it.

- [ ] **Step 2: Browser verification**

Start `.\.venv\Scripts\python.exe -m flask --app app run --port 5000`, open
`http://127.0.0.1:5000/` in the in-app Browser, and check: three bias modes
still calculate; DC/AC/Transient each run and show labelled results; axes and
units visible; netlist/log expandable; amplitude 0 shows a field error and no
plot; a broken `NGSPICE_PATH` shows an error banner when restarted with that
env var. Save a screenshot to `docs/captures/` if available and add its path
to the validation log.

- [ ] **Step 3: Write docs**

`README.md`: setup (venv, pip install -r requirements.txt, ngspice-47 location,
`NGSPICE_PATH`, `ngspice.exe` caveat), run command, baseline fixture, model
parameters, analysis reference definitions, out-of-scope list.
`AGENTS.md`: rules for AI contributors — preserve Lab 3, no fabricated data,
always show engine errors, update `docs/validation.md` when results change.

- [ ] **Step 4: Final verification and commit**

Run the full suite again and `git status`; commit docs. Then use the
finishing-a-development-branch workflow to ask about pushing.

```powershell
git add README.md AGENTS.md docs/validation.md docs/superpowers docs/captures
git commit -m "docs: record ngspice validation and browser evidence"
```
