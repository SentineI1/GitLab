# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the ENG29 2121 Lab 2 bias calculator as a small Flask app: the proven engineering core from `b9b6e8f` unchanged, a thin new web layer, and a README that matches the files on disk.

**Architecture:** One server-rendered page. `bjt_bias.py` validates form strings and solves the operating point through the Thevenin equivalent; `independent_check.py` solves the same point from base-node KCL with no shared algebra; `app.py` only moves data between those modules and the template. One Jinja template, one stylesheet, no JavaScript.

**Tech Stack:** Python 3.12, Flask 3.x, Jinja2, stdlib `unittest`, plain CSS.

**Spec:** `docs/superpowers/specs/2026-11-11-bjt-ce-bias-design.md`

## Global Constraints

- Interpreter: `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`; project venv at `.venv`.
- Only runtime dependency: `Flask>=3.0,<4.0` in `requirements.txt`.
- Test command: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`.
- Form field names exactly: `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`.
- Units: volts and ohms. Currents displayed in mA to 4 decimals; voltages and resistances to 3.
- `VCE_SAT_V = 0.2`. Cutoff when `VBB <= VBE`; the saturation test is strict `<`.
- Do not modify `electrical.py` or `test_electrical.py` (Lab 1).
- Commit directly to `main`, one commit per task.
- Restored files must be byte-identical to `b9b6e8f`.

## Review Focus

1. **All seven fields blank on POST** — expect seven "Enter a value." messages and HTTP 200, never a 500. Covered in Task 4.
2. **`VBE` at or above `VCC`** — expect a `vbe` error and no results table. Covered in Task 4.
3. **Overflow text such as `1e400`** — `float()` yields `inf`; expect "Enter a finite number." and no `inf` on the page. Covered in Task 4.
4. **Tiny `beta` (1) and huge magnitudes (`VCC=1000000`)** — expect a rendered operating point, no traceback and no `nan`. Covered in Task 3.
5. **Whitespace-padded values such as `" 12 "`** — `parse_inputs` strips, so expect acceptance. Covered in Task 4.

---

### Task 1: Runnable Python 3.12 environment

**Files:**
- Create: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: `.venv\Scripts\python.exe` with Flask 3.x importable.

- [ ] **Step 1: Create `requirements.txt`**

```text
Flask>=3.0,<4.0
```

- [ ] **Step 2: Download the Python 3.12 installer**

```powershell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile "$env:TEMP\python-3.12.10-amd64.exe" -UseBasicParsing
```

- [ ] **Step 3: Install per-user, silently**

```powershell
Start-Process -FilePath "$env:TEMP\python-3.12.10-amd64.exe" -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_pip=1","Include_test=0" -Wait
```

Expected: exit code 0, no window.

- [ ] **Step 4: Verify the interpreter**

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" --version
```

Expected: `Python 3.12.10`.

- [ ] **Step 5: Create the venv**

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
```

- [ ] **Step 6: Install Flask into the venv**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- [ ] **Step 7: Verify Flask imports**

```powershell
.\.venv\Scripts\python.exe -c "import flask; print(flask.__version__)"
```

Expected: a `3.x` version string.

- [ ] **Step 8: Commit**

```powershell
git add requirements.txt
git commit -m "build: require Flask 3.x"
```

---

### Task 2: Restore the engineering core

**Files:**
- Restore: `bjt_bias.py`, `independent_check.py`, `tests/__init__.py`, `tests/test_bjt_bias.py`, `tests/test_independent.py` from `b9b6e8f`.

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `bjt_bias.FIELDS: tuple[str, ...]`
  - `bjt_bias.VCE_SAT_V: float`
  - `bjt_bias.BiasInputError.errors: dict[str, str]`
  - `bjt_bias.BiasInputs` with `vcc_v, r1_ohm, r2_ohm, rc_ohm, re_ohm, beta, vbe_v: float`
  - `bjt_bias.BiasResult` with `vbb_v, rb_ohm, ib_ma, ic_ma, ie_ma, vb_v, vc_v, ve_v, vce_v: float`, `region: str`, `message: str`
  - `bjt_bias.parse_inputs(form: Mapping[str, str]) -> BiasInputs`
  - `bjt_bias.analyze(inputs: BiasInputs) -> BiasResult`
  - `independent_check.IndependentResult` with `ic_ma, vce_v, vb_v, ve_v, vc_v: float`
  - `independent_check.Comparison` with `ic_delta_ma, ic_relative, vce_delta_v, vce_relative: float`, `ic_match, vce_match: bool`
  - `independent_check.solve(inputs: BiasInputs) -> IndependentResult`
  - `independent_check.compare(ic_ma_thevenin, ic_ma_nodal, vce_v_thevenin, vce_v_nodal) -> Comparison`

- [ ] **Step 1: Restore the five files unchanged**

```powershell
git checkout b9b6e8f -- bjt_bias.py independent_check.py tests/__init__.py tests/test_bjt_bias.py tests/test_independent.py
```

- [ ] **Step 2: Verify nothing differs from the source commit**

```powershell
git diff --stat b9b6e8f -- bjt_bias.py independent_check.py tests/__init__.py tests/test_bjt_bias.py tests/test_independent.py
```

Expected: empty output.

- [ ] **Step 3: Run the restored tests**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_bjt_bias tests.test_independent -v
```

Expected: PASS for every test, including the worked example (`IC = 1.3236752 mA`, `VCE = 4.4462268 V`) and the exact-threshold cases.

- [ ] **Step 4: Commit**

```powershell
git add bjt_bias.py independent_check.py tests/__init__.py tests/test_bjt_bias.py tests/test_independent.py
git commit -m "feat: restore BJT bias model and independent cross-check"
```

---

### Task 3: Route, template, and results page

**Files:**
- Create: `app.py`, `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `bjt_bias.FIELDS`, `bjt_bias.parse_inputs`, `bjt_bias.analyze`, `bjt_bias.BiasInputError`, `independent_check.solve`, `independent_check.compare` (Task 2).
- Produces:
  - `app.DEFAULTS: dict[str, str]` — the seven worked-example values as strings.
  - `app.app: flask.Flask`
  - route `index` at `/`, methods `GET` and `POST`.
  - template context keys: `values: dict[str, str]`, `errors: dict[str, str]`, `result: BiasResult | None`, `independent: IndependentResult | None`, `comparison: Comparison | None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_app.py` beginning with `from app import DEFAULTS, app`, `setUp` creating `self.client = app.test_client()`, and these methods:

```python
def test_get_shows_prefilled_form(self):
    body = self.client.get("/").get_data(as_text=True)
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
    data = {**DEFAULTS, "vcc": "5", "r1": "10000", "r2": "10000",
            "rc": "1000", "re": "100", "beta": "300"}
    body = self.client.post("/", data=data).get_data(as_text=True)
    self.assertIn("Saturation", body)
    self.assertIn("DC Operating Point", body)

def test_cutoff_post_shows_warning(self):
    data = {**DEFAULTS, "r1": "100000", "r2": "1000"}
    body = self.client.post("/", data=data).get_data(as_text=True)
    self.assertIn("Cutoff", body)
    self.assertIn("DC Operating Point", body)

def test_tiny_beta_still_renders(self):
    body = self.client.post("/", data={**DEFAULTS, "beta": "1"}).get_data(as_text=True)
    self.assertIn("DC Operating Point", body)
    self.assertNotIn("nan", body.lower())

def test_huge_magnitudes_still_render(self):
    data = {**DEFAULTS, "vcc": "1000000", "r1": "1", "r2": "1",
            "rc": "1", "re": "1"}
    response = self.client.post("/", data=data)
    body = response.get_data(as_text=True)
    self.assertEqual(response.status_code, 200)
    self.assertIn("DC Operating Point", body)
    self.assertNotIn("nan", body.lower())
```

- [ ] **Step 2: Run the tests and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py`**

Signatures and behaviour, nothing else:

```python
DEFAULTS: dict[str, str]          # vcc 12, r1 47000, r2 10000, rc 4700,
                                  # re 1000, beta 150, vbe 0.7 (all strings)
app: Flask = Flask(__name__)

def _render(values, errors, result=None, independent=None, comparison=None):
    """Render index.html with the five context keys."""

@app.route("/", methods=["GET", "POST"])
def index():
    """GET: render DEFAULTS with no errors or results.
    POST: values = {name: request.form.get(name, "") for name in FIELDS};
    parse_inputs, and on BiasInputError render the same values with
    exc.errors; otherwise analyze, solve, compare and render results."""
```

No physics and no unit conversion in this module.

- [ ] **Step 4: Implement `templates/index.html`**

One page, no JavaScript:

- `<form method="post" action="/">` with seven labelled `<input type="number" step="any" name="…" value="{{ values.<name> }}">` fields: VCC (V), R1 (ohm), R2 (ohm), RC (ohm), RE (ohm), beta, VBE (V).
- A submit button labelled `Calculate`.
- A results section rendered only `{% if result %}`:
  - heading `DC Operating Point`;
  - region badge `<span class="badge badge-{{ result.region }}">{{ result.region|capitalize }}</span>`;
  - `{{ result.message }}`;
  - table of `VBB, RB, IB, IC, IE, VB, VC, VE, VCE` with units, currents `{{ "%.4f"|format(...) }}` in mA, voltages and resistances `{{ "%.3f"|format(...) }}`.
- A cross-check block rendered only `{% if comparison %}`: heading containing the words `Thevenin` and `Nodal`, both `IC` values, both `VCE` values, absolute and relative deltas, and a match line stating whether the two methods agree.
- Title and `<h1>` both mention the bias calculator.

- [ ] **Step 5: Run the tests and confirm they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: PASS for all six tests.

- [ ] **Step 6: Commit**

```powershell
git add app.py templates/index.html tests/test_app.py
git commit -m "feat: add bias calculator page and results rendering"
```

---

### Task 4: Validation errors in the page

**Files:**
- Modify: `templates/index.html` (error markup)
- Modify: `tests/test_app.py` (add tests)

**Interfaces:**
- Consumes: `errors: dict[str, str]` from Task 3.
- Produces: nothing new.

- [ ] **Step 1: Add the failing tests**

```python
def test_invalid_post_shows_error_and_preserves_values(self):
    body = self.client.post("/", data={**DEFAULTS, "vcc": "0"}).get_data(as_text=True)
    self.assertNotIn("DC Operating Point", body)
    self.assertIn("greater than 0", body)
    self.assertIn('value="47000"', body)

def test_blank_form_reports_every_field(self):
    body = self.client.post("/", data={}).get_data(as_text=True)
    self.assertEqual(body.count("Enter a value."), 7)
    self.assertNotIn("DC Operating Point", body)

def test_vbe_must_be_below_vcc(self):
    body = self.client.post("/", data={**DEFAULTS, "vbe": "12"}).get_data(as_text=True)
    self.assertIn("VBE must be less than VCC.", body)
    self.assertNotIn("DC Operating Point", body)

def test_overflow_text_is_rejected(self):
    body = self.client.post("/", data={**DEFAULTS, "r1": "1e400"}).get_data(as_text=True)
    self.assertIn("Enter a finite number.", body)
    self.assertNotIn("DC Operating Point", body)

def test_whitespace_is_accepted(self):
    body = self.client.post("/", data={**DEFAULTS, "vcc": " 12 "}).get_data(as_text=True)
    self.assertIn("DC Operating Point", body)
```

- [ ] **Step 2: Run them and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: the four error tests FAIL because no messages are rendered; `test_whitespace_is_accepted` passes already.

- [ ] **Step 3: Render errors in `templates/index.html`**

Next to each input, add `{% if errors.<name> %}<p class="field-error">{{ errors.<name> }}</p>{% endif %}`. Keep submitted values in `value="{{ values.<name> }}"`. Do not render the results or cross-check sections when `errors` is non-empty.

- [ ] **Step 4: Run the tests and confirm they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: PASS for all eleven tests.

- [ ] **Step 5: Commit**

```powershell
git add templates/index.html tests/test_app.py
git commit -m "feat: show per-field validation errors"
```

---

### Task 5: Stylesheet

**Files:**
- Create: `static/style.css`
- Modify: `templates/index.html` (link)
- Modify: `tests/test_app.py` (add tests)

**Interfaces:**
- Consumes: template from Task 3/4.
- Produces: `/static/style.css` served by Flask's default static route.

- [ ] **Step 1: Add the failing tests**

```python
def test_stylesheet_is_linked(self):
    body = self.client.get("/").get_data(as_text=True)
    self.assertIn("style.css", body)

def test_stylesheet_is_served(self):
    response = self.client.get("/static/style.css")
    self.assertEqual(response.status_code, 200)
    self.assertIn("text/css", response.content_type)
    self.assertIn(".badge", response.get_data(as_text=True))

def test_region_badge_class_is_present(self):
    body = self.client.post("/", data=DEFAULTS).get_data(as_text=True)
    self.assertIn("badge-active", body)
```

- [ ] **Step 2: Run them and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: all three FAIL.

- [ ] **Step 3: Create `static/style.css` (80 lines maximum)**

Rules that must exist: page font and background; a centred container with a readable max width; a two-column form grid with full-width submit; `.field-error` in a warning colour; `.badge` base rule plus `.badge-active` (green), `.badge-cutoff` (grey), `.badge-saturation` (amber); a bordered results table with right-aligned numeric cells; a muted cross-check block.

- [ ] **Step 4: Link the stylesheet in `templates/index.html`**

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

- [ ] **Step 5: Run the tests and confirm they pass**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

Expected: PASS for all fourteen tests.

- [ ] **Step 6: Commit**

```powershell
git add static/style.css templates/index.html tests/test_app.py
git commit -m "feat: style the bias calculator page"
```

---

### Task 6: README, full verification, live demo, push

**Files:**
- Modify: `README.md` (rewrite)

**Interfaces:**
- Consumes: everything above.
- Produces: a README that matches the files on disk.

- [ ] **Step 1: Run the full suite**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Expected: PASS, no failures or errors: 20 restored tests plus the 14 web tests.

- [ ] **Step 2: Start the server in the background**

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

- [ ] **Step 3: Verify the live page**

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing).StatusCode
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Post -Body @{vcc="12";r1="47000";r2="10000";rc="4700";re="1000";beta="150";vbe="0.7"} -UseBasicParsing).Content | Select-String "1.3237|4.446|Active"
```

Expected: `200`, then all three patterns found.

- [ ] **Step 4: Rewrite `README.md`**

Cover, in about 80 lines: what the app is and is not; the circuit in one ASCII sketch; the seven inputs with units and rules; the nine outputs with units and display precision; the region rules and that nothing is clamped; the cross-check and its tolerance; setup with the exact interpreter path; run; test; the worked example table (`IC = 1.3237 mA`, `VCE = 4.446 V`, active); the file list; links to the design doc and this plan. Remove every reference to deleted files and to Lab 1 behaviour that the app does not have.

- [ ] **Step 5: Stop the server and confirm a clean tree**

```powershell
git status --short
```

Expected: only the README modification and the untracked `docs/superpowers/` files.

- [ ] **Step 6: Commit**

```powershell
git add README.md docs/superpowers
git commit -m "docs: describe the rebuilt bias calculator"
```

- [ ] **Step 7: Push**

```powershell
git push origin main
```

Expected: `main -> main`. If credentials or the network block it, report the push as the single open item and leave the commits in place.

- [ ] **Step 8: Verify the remote**

```powershell
git log --oneline -1 origin/main
```

Expected: the README commit.
