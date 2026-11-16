# Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fixed-bias and emitter-bias solvers beside the existing divider, selected by a `mode` field, without changing the divider result or the existing tests.

**Architecture:** A new `bias_modes.py` holds the three solvers and per-mode validation, returning dicts whose keys carry units. `solve_divider()` delegates to `bjt_bias.analyze()`. `app.py` dispatches on `mode`; the template renders every input and guards divider-only rows and the schematic.

**Tech Stack:** Flask 3.1 / Jinja2 / plain CSS / Python `unittest` (existing only).

**Spec:** `docs/superpowers/specs/2026-11-16-bias-modes-design.md`

## Global Constraints

- Do not modify `bjt_bias.py`, `independent_check.py`, or any file in `tests/`.
- Do not add new `unittest` tests; verification is a Browser pass.
- Divider numbers must be identical to today (same `analyze()` call).
- Result dict keys: `mode`, `ib_ma`, `ic_ma`, `ie_ma`, `vb_v`, `vc_v`, `ve_v`, `vce_v`, `region`, `message`; divider adds `vbb_v`, `rb_ohm`.
- Currents are in mA, voltages in V, resistances in ohm.

## Review Focus

1. **Divider regression** — 43 existing tests pass unchanged; worked example still `1.3237` mA / `4.446` V / Active.
2. **Mode switching** — changing `mode` keeps the common values and validates only that mode's fields.
3. **Blank form** — exactly seven "Enter a value." messages in divider mode, no 500.
4. **Per-mode fields** — fixed ignores `r1/r2/re`; emitter ignores `r1/r2`; divider ignores `rb`.
5. **Cross-check** — appears only in divider mode.

---

### Task 1: Solvers and per-mode validation

**Files:**
- Create: `bias_modes.py`

**Interfaces:**
- Consumes: `bjt_bias.parse_inputs`, `bjt_bias.analyze`, `bjt_bias.BiasInputs`, `bjt_bias.BiasInputError`, `bjt_bias._parse_field`, `bjt_bias.VCE_SAT_V`, and the three region messages.
- Produces: `MODES`, `MODE_LABELS`, `FIELDS_BY_MODE`, `parse_for_mode(mode, form) -> dict[str, float]`, `solve_divider(values) -> dict`, `solve_fixed(values) -> dict`, `solve_emitter(values) -> dict`, `solve(mode, values) -> dict`.

- [ ] **Step 1: Create `bias_modes.py`** with the module docstring, constants, `parse_for_mode`, `_classify`, `_result`, the three solvers, and `solve`. `solve_divider` must call `analyze()` and copy its fields; fixed/emitter follow the spec formulas and multiply currents by 1000 only when building the dict.

- [ ] **Step 2: Smoke-check the solvers**

Run: `.\.venv\Scripts\python.exe -c "from bias_modes import *; d=parse_for_mode('divider', {'vcc':'12','r1':'47000','r2':'10000','rc':'4700','re':'1000','beta':'150','vbe':'0.7'}); print(solve('divider', d)); f=parse_for_mode('fixed', {'vcc':'12','rb':'1200000','rc':'4700','beta':'150','vbe':'0.7'}); print(solve('fixed', f)); e=parse_for_mode('emitter', {'vcc':'12','rb':'1200000','rc':'4700','re':'1000','beta':'150','vbe':'0.7'}); print(solve('emitter', e))"`

Expected: three dicts, divider `ic_ma` ≈ 1.3237 and `vce_v` ≈ 4.4462; fixed/emitter active.

---

### Task 2: Route, template, styles

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/style.css`

**Interfaces:**
- Consumes: `bias_modes` from Task 1.
- Produces: `mode` in the template context via `values.mode`; `mode_labels` in the render context.

- [ ] **Step 1: Update `app.py`** — import `bias_modes`; add `"rb": "1200000"` and `"mode": "divider"` to `DEFAULTS`; read `mode`, validate with `parse_for_mode`, call `solve`, and build `BiasInputs` + `independent_check` only for divider.

- [ ] **Step 2: Update `templates/index.html`** — add the `mode` select (full width), add the `rb` input with its error slot, annotate the mode-specific labels, guard the VBB/RB rows with `is defined`, render the schematic only when `values.mode == "divider"`, and add `workspace-single` when it is absent.

- [ ] **Step 3: Update `static/style.css`** — add `.field-wide`, `select`, and `.workspace-single` rules.

- [ ] **Step 4: Run the existing suite**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`

Expected: `Ran 43 tests ... OK`.

---

### Task 3: README and Browser verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the three modes** — add a short "Bias modes" section with the two new formula blocks and the result keys.

- [ ] **Step 2: Restart the server and verify each mode**

Run: `.\.venv\Scripts\python.exe -m flask --app app run --port 5000`

Then POST each mode and confirm the page renders the operating point, the region badge, and the divider-only rows/cross-check:

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Post -Body @{mode="divider";vcc="12";r1="47000";r2="10000";rc="4700";re="1000";beta="150";vbe="0.7"} -UseBasicParsing).Content
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Post -Body @{mode="fixed";vcc="12";rb="1200000";rc="4700";beta="150";vbe="0.7"} -UseBasicParsing).Content
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Post -Body @{mode="emitter";vcc="12";rb="1200000";rc="4700";re="1000";beta="150";vbe="0.7"} -UseBasicParsing).Content
```

Expected: divider shows `1.3237` / `4.446` / `Active` and the cross-check; fixed and emitter show their own operating point, `Active`, and no cross-check.

- [ ] **Step 3: Commit**

```powershell
git add bias_modes.py app.py templates/index.html static/style.css README.md docs/superpowers
git commit -m "feat: add fixed and emitter bias modes"
```
