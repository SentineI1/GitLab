# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Flask app that computes and cross-checks the DC operating point of an NPN common-emitter bias circuit, with units, validation, and region warnings.

**Architecture:** `bjt_bias.py` owns validation, the Thevenin/β solve, and region classification. `independent_check.py` solves the base-node KCL with no shared algebra and compares results. `app.py` is routes only; one Jinja template and one CSS file render the form, results, region badge, and cross-check.

**Tech Stack:** Python 3.12, Flask 3.x, stdlib `unittest`, server-rendered Jinja HTML, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Python 3.12; Flask `>=3.0,<4.0` is the only runtime dependency.
- Tests use stdlib `unittest`, run with `python -m unittest discover -s tests -t .`.
- Lab 1 files `electrical.py` and `test_electrical.py` must not be modified.
- No JavaScript, CDN assets, database, or AC/transient/FET analysis.
- Currents in mA (4 decimal places), voltages in V (3 decimal places), resistances in ohm.
- `VCE_SAT_V = 0.2` in `bjt_bias.py`.
- Validation: `VCC > 0`; `R1`, `R2`, `RC`, `RE > 0`; `beta > 0`; `0 < VBE < VCC`; reject blank, non-numeric, `NaN`, `inf`.
- Commit to `main` and push to `origin`. Git is at `C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe`.

## Review Focus

These are the failure modes most likely to bite a user, each pinned to a task:

1. `VBB == VBE` yields exact `IC = 0` on one path and floating-point residue on the other — must not show a false mismatch (Task 4).
2. Blank, non-numeric, `NaN`, or `inf` form input — must show an inline error, never a 500 (Tasks 2 and 5).
3. `VBE >= VCC` — must be rejected, not produce negative currents (Task 2).
4. A saturated result with negative `VCE` — must still render with a warning (Tasks 3 and 5).
5. An invalid POST — must preserve typed values and show no stale results (Task 5).

---

### Task 1: Baseline docs and dependency file

**Files:**
- Create: `requirements.txt`
- Commit: `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`, `docs/superpowers/plans/2026-11-10-bjt-ce-bias.md`

**Interfaces:**
- Consumes: approved design doc.
- Produces: repository baseline for all later tasks.

- [ ] **Step 1: Create `requirements.txt`**

```text
Flask>=3.0,<4.0
```

- [ ] **Step 2: Commit the design, plan, and dependency file**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add requirements.txt docs/superpowers
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "docs: add BJT bias design and implementation plan"
```

---

### Task 2: Input parsing and validation

**Files:**
- Create: `bjt_bias.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `BiasInputError(ValueError)` with attribute `errors: dict[str, str]` keyed by form field name (`vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`).
  - `BiasInputs` frozen dataclass with float fields `vcc_v`, `r1_ohm`, `r2_ohm`, `rc_ohm`, `re_ohm`, `beta`, `vbe_v`.
  - `parse_inputs(form: Mapping[str, str]) -> BiasInputs`, raising `BiasInputError`.

- [ ] **Step 1: Write the failing tests**

Create an empty `tests/__init__.py`, then create `tests/test_bjt_bias.py`:

```python
import unittest

from bjt_bias import BiasInputError, parse_inputs

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


class TestParseInputs(unittest.TestCase):
    def test_parses_valid_form(self):
        inputs = parse_inputs(VALID)
        self.assertEqual(inputs.vcc_v, 12.0)
        self.assertEqual(inputs.r1_ohm, 47000.0)
        self.assertEqual(inputs.r2_ohm, 10000.0)
        self.assertEqual(inputs.rc_ohm, 4700.0)
        self.assertEqual(inputs.re_ohm, 1000.0)
        self.assertEqual(inputs.beta, 150.0)
        self.assertEqual(inputs.vbe_v, 0.7)

    def test_blank_field_is_reported(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "r1": "   "})
        self.assertEqual(ctx.exception.errors["r1"], "Enter a value.")

    def test_non_numeric_field_is_reported(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "rc": "abc"})
        self.assertEqual(ctx.exception.errors["rc"], "Enter a finite number.")

    def test_nan_and_inf_are_rejected(self):
        for bad in ("nan", "inf", "-inf"):
            with self.subTest(bad=bad):
                with self.assertRaises(BiasInputError) as ctx:
                    parse_inputs({**VALID, "beta": bad})
                self.assertIn("beta", ctx.exception.errors)

    def test_non_positive_resistances_are_rejected(self):
        for field, label in (("r1", "R1"), ("r2", "R2"), ("rc", "RC"), ("re", "RE")):
            for bad in ("0", "-5"):
                with self.subTest(field=field, bad=bad):
                    with self.assertRaises(BiasInputError) as ctx:
                        parse_inputs({**VALID, field: bad})
                    self.assertEqual(
                        ctx.exception.errors[field],
                        f"{label} must be greater than 0.",
                    )

    def test_vcc_must_be_positive(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "vcc": "0"})
        self.assertEqual(ctx.exception.errors["vcc"], "VCC must be greater than 0.")

    def test_beta_must_be_positive(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "beta": "-1"})
        self.assertEqual(ctx.exception.errors["beta"], "beta must be greater than 0.")

    def test_vbe_must_be_between_zero_and_vcc(self):
        for bad in ("0", "12", "13"):
            with self.subTest(bad=bad):
                with self.assertRaises(BiasInputError) as ctx:
                    parse_inputs({**VALID, "vbe": bad})
                self.assertIn("vbe", ctx.exception.errors)

    def test_collects_multiple_errors(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "vcc": "0", "beta": "-1"})
        self.assertGreaterEqual(len(ctx.exception.errors), 2)
        self.assertIn("vcc", ctx.exception.errors)
        self.assertIn("beta", ctx.exception.errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_bjt_bias -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt_bias'`.

- [ ] **Step 3: Implement `bjt_bias.py`**

Implement the `BiasInputError` class and `BiasInputs` dataclass exactly as described in **Interfaces**, then `parse_inputs`. Parse each field with `float()`; strip the value first; a blank string is `"Enter a value."`; a `ValueError` or non-finite result is `"Enter a finite number."`. Apply the range rules from **Global Constraints** in form order and collect every message in one `BiasInputError`. Check `VBE < VCC` only when `vcc` parsed successfully.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_bjt_bias -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add bjt_bias.py tests/__init__.py tests/test_bjt_bias.py
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "feat: validate BJT bias inputs"
```

---

### Task 3: Thevenin solve and region classification

**Files:**
- Modify: `bjt_bias.py`
- Modify: `tests/test_bjt_bias.py`

**Interfaces:**
- Consumes: `BiasInputs` and `parse_inputs` from Task 2.
- Produces:
  - `VCE_SAT_V = 0.2`
  - `BiasResult` frozen dataclass with float fields `vbb_v`, `rb_ohm`, `ib_ma`, `ic_ma`, `ie_ma`, `vb_v`, `vc_v`, `ve_v`, `vce_v`, plus `region: str` (`"active"`, `"cutoff"`, or `"saturation"`) and `message: str`.
  - `analyze(inputs: BiasInputs) -> BiasResult`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bjt_bias.py` (update the import line to `from bjt_bias import BiasInputError, VCE_SAT_V, analyze, parse_inputs`):

```python
def make(**overrides):
    return parse_inputs({**VALID, **overrides})


class TestAnalyze(unittest.TestCase):
    def test_worked_example_is_active(self):
        result = analyze(make())
        self.assertEqual(result.region, "active")
        self.assertIn("active", result.message.lower())
        self.assertAlmostEqual(result.vbb_v, 2.1052632, delta=1e-6)
        self.assertAlmostEqual(result.rb_ohm, 8245.614035, delta=1e-3)
        self.assertAlmostEqual(result.ib_ma, 0.0088245, delta=1e-7)
        self.assertAlmostEqual(result.ic_ma, 1.3236752, delta=1e-6)
        self.assertAlmostEqual(result.ie_ma, 1.3324997, delta=1e-6)
        self.assertAlmostEqual(result.vb_v, 2.0324997, delta=1e-6)
        self.assertAlmostEqual(result.vc_v, 5.7787265, delta=1e-6)
        self.assertAlmostEqual(result.ve_v, 1.3324997, delta=1e-6)
        self.assertAlmostEqual(result.vce_v, 4.4462268, delta=1e-6)

    def test_cutoff_when_vbb_below_vbe(self):
        result = analyze(make(r1="100000", r2="1000"))
        self.assertEqual(result.region, "cutoff")
        self.assertIn("cutoff", result.message.lower())
        self.assertGreater(result.vce_v, VCE_SAT_V)

    def test_cutoff_boundary_has_zero_current(self):
        result = analyze(make(vcc="7", r1="9000", r2="1000"))
        self.assertEqual(result.region, "cutoff")
        self.assertAlmostEqual(result.ic_ma, 0.0, places=12)
        self.assertAlmostEqual(result.vce_v, 7.0, places=12)

    def test_saturation_when_vce_below_threshold(self):
        result = analyze(
            make(vcc="5", r1="10000", r2="10000", rc="1000", re="100", beta="300")
        )
        self.assertEqual(result.region, "saturation")
        self.assertIn("saturation", result.message.lower())
        self.assertLess(result.vce_v, VCE_SAT_V)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_bjt_bias -v`
Expected: FAIL with `ImportError` for `VCE_SAT_V` / `analyze`.

- [ ] **Step 3: Implement the solve**

Add `VCE_SAT_V = 0.2` and the `BiasResult` dataclass, then `analyze` using exactly:

```text
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

Convert `IB`, `IC`, `IE` from A to mA by multiplying by 1000. Classify in this order: `VBB <= VBE` → `"cutoff"`; else `VCE < VCE_SAT_V` → `"saturation"`; else `"active"`. Messages: `"Cutoff: the base-emitter junction is not forward biased; the transistor is off."`, `"Saturation: VCE is below VCE(sat); the active-region result is not the true operating point."`, `"Active: the transistor is in the active region."`. Do not clamp any value.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_bjt_bias -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add bjt_bias.py tests/test_bjt_bias.py
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "feat: solve BJT bias operating point"
```

---

### Task 4: Independent KCL solve and comparison

**Files:**
- Create: `independent_check.py`
- Create: `tests/test_independent.py`

**Interfaces:**
- Consumes: `BiasInputs` from Task 2; `analyze` and `BiasResult` from Task 3.
- Produces:
  - `IndependentResult` frozen dataclass with float fields `ic_ma`, `vce_v`, `vb_v`, `ve_v`, `vc_v`.
  - `solve(inputs: BiasInputs) -> IndependentResult`
  - `Comparison` frozen dataclass with float fields `ic_delta_ma`, `ic_relative`, `vce_delta_v`, `vce_relative`, and bool fields `ic_match`, `vce_match`.
  - `compare(ic_ma_thevenin, ic_ma_nodal, vce_v_thevenin, vce_v_nodal) -> Comparison`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_independent.py`:

```python
import unittest

from bjt_bias import analyze, parse_inputs
from independent_check import compare, solve

CASES = {
    "active": {
        "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
    "cutoff": {
        "vcc": "12", "r1": "100000", "r2": "1000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
    "saturation": {
        "vcc": "5", "r1": "10000", "r2": "10000", "rc": "1000",
        "re": "100", "beta": "300", "vbe": "0.7",
    },
    "boundary_vbb_equals_vbe": {
        "vcc": "7", "r1": "9000", "r2": "1000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
}


class TestIndependentAgreement(unittest.TestCase):
    def test_methods_agree_across_cases(self):
        for name, form in CASES.items():
            with self.subTest(case=name):
                inputs = parse_inputs(form)
                main = analyze(inputs)
                other = solve(inputs)
                comparison = compare(
                    main.ic_ma, other.ic_ma, main.vce_v, other.vce_v
                )
                self.assertTrue(comparison.ic_match, f"IC mismatch in {name}")
                self.assertTrue(comparison.vce_match, f"VCE mismatch in {name}")
                self.assertLessEqual(comparison.ic_relative, 1e-6)
                self.assertLessEqual(comparison.vce_relative, 1e-6)


class TestCompare(unittest.TestCase):
    def test_exact_zeros_match(self):
        comparison = compare(0.0, 1e-12, 0.0, 1e-13)
        self.assertTrue(comparison.ic_match)
        self.assertTrue(comparison.vce_match)

    def test_real_difference_does_not_match(self):
        comparison = compare(1.0, 2.0, 1.0, 1.0)
        self.assertFalse(comparison.ic_match)
        self.assertAlmostEqual(comparison.ic_relative, 0.5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_independent -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'independent_check'`.

- [ ] **Step 3: Implement `independent_check.py`**

`solve` must use this base-node KCL path and must not import or call anything from `bjt_bias` except the `BiasInputs` type:

```text
VB = (VCC/R1 + VBE/((1+beta)*RE)) / (1/R1 + 1/R2 + 1/((1+beta)*RE))
VE = VB - VBE
IE = VE / RE
IB = IE / (1 + beta)
IC = beta * IB
VC = VCC - IC * RC
VCE = VC - VE
```

Convert `IC` from A to mA. `compare` computes `delta = abs(a - b)`. For currents use an absolute floor of `1e-9` mA; for voltages use `1e-12` V. Two values match when both magnitudes are at or below the floor, or when `delta / max(abs(a), abs(b)) <= 1e-6`. When both are below the floor, report relative difference `0.0`. Otherwise report the computed ratio.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_independent -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add independent_check.py tests/test_independent.py
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "feat: add independent bias cross-check"
```

---

### Task 5: Flask routes, template, and CSS

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `parse_inputs`, `BiasInputError`, `analyze` from Task 2/3; `solve`, `compare` from Task 4.
- Produces: Flask instance `app`; `GET /` and `POST /`. Template context keys: `values` (raw form strings), `errors` (field → message), `result` (`BiasResult` or `None`), `independent` (`IndependentResult` or `None`), `comparison` (`Comparison` or `None`).

- [ ] **Step 1: Create the virtual environment and install Flask**

Run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_app.py`:

```python
import unittest

from app import app

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_shows_prefilled_form(self):
        response = self.client.get("/")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="vcc"', body)
        self.assertIn('value="12"', body)
        self.assertNotIn("DC Operating Point", body)

    def test_valid_post_shows_operating_point(self):
        response = self.client.post("/", data=DEFAULTS)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("DC Operating Point", body)
        self.assertIn("Active", body)
        self.assertIn("1.3237", body)
        self.assertIn("4.446", body)
        self.assertIn("Thevenin", body)
        self.assertIn("Nodal", body)

    def test_saturation_post_shows_warning(self):
        data = {
            **DEFAULTS, "vcc": "5", "r1": "10000", "r2": "10000",
            "rc": "1000", "re": "100", "beta": "300",
        }
        response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Saturation", body)
        self.assertIn("DC Operating Point", body)

    def test_invalid_post_shows_error_and_preserves_values(self):
        response = self.client.post("/", data={**DEFAULTS, "vcc": "0"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("DC Operating Point", body)
        self.assertIn("greater than 0", body)
        self.assertIn('value="47000"', body)

    def test_non_numeric_post_shows_error(self):
        response = self.client.post("/", data={**DEFAULTS, "r1": "abc"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("DC Operating Point", body)
        self.assertIn("Enter a finite number.", body)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 4: Implement `app.py`, `templates/index.html`, and `static/style.css`**

`app.py` defines `DEFAULTS` with the seven string values from the spec (`12`, `47000`, `10000`, `4700`, `1000`, `150`, `0.7`). `GET /` renders `index.html` with `values=DEFAULTS`, `errors={}`, and the three result keys `None`. `POST /` rebuilds `values` from `request.form` for all seven fields, calls `parse_inputs`, and on `BiasInputError` re-renders with `errors=exc.errors` and results `None`. On success it calls `analyze`, `solve`, and `compare`, then renders with all results.

`templates/index.html` must:
- Use `{{ url_for('static', filename='style.css') }}` and no other assets.
- Render seven labelled inputs named `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`, each with `value="{{ values.<field> }}"` and its error message beneath when `errors` has that field.
- Show the error list when `errors` is non-empty.
- Only when `result` is set: the heading `DC Operating Point`, a region badge containing `{{ result.region|capitalize }}`, `{{ result.message }}`, and a table with units: `VBB`/`RB`/`IB`/`IC`/`IE`/`VB`/`VC`/`VE`/`VCE`, using `"%.4f"|format(...)` for mA and `"%.3f"|format(...)` for V and ohm.
- Only when `comparison` is set: a table labelled `Thevenin` and `Nodal` with both `IC` and `VCE`, the deltas, the relative differences, and a match indicator.

`static/style.css` gives the form and tables a readable layout and three badge colours: `.badge-active` green, `.badge-cutoff` amber, `.badge-saturation` red.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add app.py templates static tests/test_app.py
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "feat: add BJT bias web interface"
```

---

### Task 6: README, live check, and push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything from Tasks 2–5.
- Produces: runnable documented app and pushed `main`.

- [ ] **Step 1: Write `README.md`**

Include: what the app does, the circuit inputs and outputs, setup commands (`python -m venv .venv`, install from `requirements.txt`), run command (`.\.venv\Scripts\python.exe -m flask --app app run --port 5000`), URL `http://127.0.0.1:5000`, test command, and the worked example (`VCC=12`, `R1=47000`, `R2=10000`, `RC=4700`, `RE=1000`, `beta=150`, `VBE=0.7` → `IC ≈ 1.3237 mA`, `VCE ≈ 4.446 V`, active).

- [ ] **Step 2: Run the full suite**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`
Expected: all tests PASS.

Then confirm Lab 1 is untouched and still passes:

Run: `.\.venv\Scripts\python.exe -m unittest test_electrical -v`
Expected: all Lab 1 tests PASS.

- [ ] **Step 3: Live smoke test**

Start the server in the background, request the page, and confirm `200`:

```powershell
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","flask","--app","app","run","--port","5000" -PassThru
Start-Sleep -Seconds 3
(Invoke-WebRequest http://127.0.0.1:5000/).StatusCode
```

Expected: `200`. Stop the server process afterwards.

- [ ] **Step 4: Commit and push**

```powershell
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' add README.md
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' commit -m "docs: document BJT bias app"
& 'C:\Users\B6830021\AppData\Local\Programs\Git\bin\git.exe' push origin main
```

If the push asks for credentials or fails, stop and report the exact error; do not retry with guessed credentials.

---

## Self-Review

- **Spec coverage:** inputs/validation (Task 2), Thevenin/β output (Task 3), region warnings (Task 3), independent comparison (Task 4), units and UI (Task 5), tests (Tasks 2–5), delivery/push (Task 6). All spec sections map to a task.
- **Step scan:** every step has one action and a checkable result; no "handle edge cases" or TBD lines.
- **Type consistency:** `BiasInputs`, `BiasResult`, `IndependentResult`, and `Comparison` field names match across Tasks 2–5; `compare` takes the four primitives used by the route and tests.
- **Review Focus:** each of the five failure modes has a named test in its owning task.
- **Proportion:** the plan is longer than the spec because it pins exact tests and values, but it does not transcribe the implementation bodies.
