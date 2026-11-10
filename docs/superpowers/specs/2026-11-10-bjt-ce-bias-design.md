# BJT Common-Emitter DC Bias Web App — Design

- **Date:** 2026-11-10
- **Course:** ENG29 2121, Lab 2
- **Status:** Approved (2026-11-10)
- **Repo:** `SentineI1/GitLab`, branch `main`

## Intent

A small, working Flask app that lets a student enter the seven bias values of an
NPN common-emitter circuit and see the DC operating point, with units, input
validation, and a warning when the transistor is not in the active region. The
app also runs a second, independently coded calculation and shows both results
side by side so the student can confirm the answer is not an artefact of one
equation path.

The point is a trustworthy, demonstrable lab deliverable — not a circuit
simulator.

## Goals

- Accept `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE` from a web form.
- Return `VBB`, `RB`, `IB`, `IC`, `IE`, `VB`, `VC`, `VE`, `VCE` with units.
- Classify the region as active, cutoff, or saturation and warn otherwise.
- Reject invalid input with a clear message, without losing what was typed.
- Cross-check every result with a second implementation and show the delta.
- Keep engineering logic, routes, templates, CSS, and tests in separate files.
- Run locally and be committed/pushed to GitHub today.

## Non-goals

- No AC, small-signal, transient, or frequency analysis.
- No schematic editor, netlist, or arbitrary circuit solving.
- No FET/MOSFET support.
- No database, login, persistence, or history.
- No JavaScript framework, charting, or SPICE integration.

## Anti-goals

- A result that looks plausible but cannot be reproduced by hand.
- Silent wrong answers when the transistor is saturated or cut off.
- A single monolithic `app.py` that mixes physics with HTTP.

## Constraints

- Python 3.12 (installed), Flask not yet installed; use a local `.venv`.
- Only runtime dependency: Flask 3.x.
- Tests use the standard library `unittest`, matching the existing
  `test_electrical.py` in the repo.
- Lab 1 files (`electrical.py`, `test_electrical.py`) must not be modified.
- Existing repo history commits directly to `main`; this work follows suit.
- `git` is installed at `C:\Users\B6830021\AppData\Local\Programs\Git` but is not
  on `PATH`; invoke it by full path.

## Approaches considered

### Web layer

- **Chosen — server-rendered form.** `GET /` shows the form; `POST /` validates,
  computes, and re-renders the same template with values and results. No
  JavaScript. One template, one route, easy to test with Flask's test client.
- Rejected — JSON API plus `fetch`. Adds a JS layer and a second test surface
  for no lab value.
- Rejected — separate form and results pages. Loses the user's inputs on a
  validation error and needs a second template.

### Region handling

- **Chosen — one linear solve, then classify.** Solve the active-region
  equations once, then label the result. Cutoff and saturation produce warnings;
  the saturated operating point is not recomputed.
- Rejected — iterative piecewise solve clamping at `VCE(sat)`. Correct but out
  of scope for this lab.
- Rejected — assume active region only. Would miss a stated requirement.

### Independent calculation

- **Chosen — second method in the app.** A separate module solves the base-node
  KCL directly, without the Thevenin reduction. The route calls both and the
  template shows the two results and their difference.
- Rejected — reference values in tests only. Not visible in the demo.
- Rejected — separate CLI script. Extra surface without a UI benefit.

## Design

### Circuit and model

NPN common-emitter bias: `VCC` feeds `R1` (to base) and `RC` (to collector);
`R2` runs base to ground; `RE` runs emitter to ground. `VBE` and `beta` are
given constants. The transistor is modelled as a fixed `VBE` drop and
`IC = beta * IB`, valid in the active region.

Thevenin reduction of the base divider:

```
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

### Independent method

Solve the base node directly with KCL, using `IE = (VB - VBE) / RE` and
`IB = IE / (1 + beta)`:

```
VB = (VCC/R1 + VBE/((1+beta)*RE)) / (1/R1 + 1/R2 + 1/((1+beta)*RE))
VE = VB - VBE
IE = VE / RE
IB = IE / (1 + beta)
IC = beta * IB
VC = VCC - IC * RC
VCE = VC - VE
```

This shares no algebra or helper functions with the Thevenin path. Agreement
between the two is the check.

Comparison helper: two values match when their relative difference is
`<= 1e-6`, using `max(|a|, |b|)` as the denominator, or when both magnitudes
are at or below an absolute floor (`1e-12` A for currents, `1e-12` V for
voltages). The floor matters at the boundaries: at `VBB == VBE` the Thevenin
path gives `IC = 0` exactly while the nodal path can leave a tiny
floating-point residue, and a bare relative difference would call that a
mismatch.

### Region classification

| Condition | Region | Message |
|---|---|---|
| `VBB <= VBE` | Cutoff | Base-emitter junction not forward biased; transistor is off. |
| `VCE < 0.2 V` | Saturation | `VCE` below `VCE(sat)`; the active-region result is not the true operating point. |
| otherwise | Active | Transistor is in the active region. |

The linear solution is always reported. In cutoff it may contain non-positive
currents, and the warning says so; values are not clamped or silently replaced.
`0.2 V` is a named constant (`VCE_SAT_V`) so it is easy to change.

### Validation

All inputs are required. Parse as float; reject blank, non-numeric, `NaN`, and
infinite values. Ranges:

- `VCC > 0`
- `R1 > 0`, `R2 > 0`, `RC > 0`, `RE > 0` (ohms)
- `beta > 0`
- `0 < VBE < VCC`

Each failure returns a human-readable message naming the field. All messages are
collected so the user can fix several at once. Invalid input never reaches the
engineering functions.

### Output and units

| Quantity | Unit |
|---|---|
| `VBB`, `VBE`, `VB`, `VC`, `VE`, `VCE` | V |
| `RB`, `R1`, `R2`, `RC`, `RE` | ohm |
| `IB`, `IC`, `IE` | mA |

Display to four decimal places for currents (so `IB` in the tens of microamps is
still visible) and three for voltages. The template receives raw `BiasResult` /
`IndependentResult` / `Comparison` objects and formats them (`"%.3f"` for
V/ohm, `"%.4f"` for mA).

### User interface

One page (`templates/index.html`):

1. Heading and a one-line description of the circuit.
2. Form with seven labelled numeric fields, prefilled with a working example:
   `VCC=12`, `R1=47000`, `R2=10000`, `RC=4700`, `RE=1000`, `beta=150`,
   `VBE=0.7`. This makes the first `GET` demonstrable without typing.
3. Inline error list when validation fails; the submitted values stay in the
   form.
4. On success: a region badge (green active, amber cutoff, red saturation) with
   its message, a results table with units, and a cross-check table showing
   Thevenin vs nodal for `IC` and `VCE`, the absolute delta, the relative delta,
   and a match indicator.

`static/style.css` handles layout and the three badge colours. No external
fonts, CDNs, or JS.

### Files

```
app.py                       # Flask app and routes only
bjt_bias.py                  # validation, Thevenin solve, classification
independent_check.py         # base-node KCL solve, no shared algebra
templates/index.html
static/style.css
tests/test_bjt_bias.py       # model, regions, validation
tests/test_independent.py    # agreement across cases
tests/test_app.py            # GET, valid POST, invalid POST
requirements.txt             # Flask 3.x
README.md                    # run instructions and example values
docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
```

### Worked example (test anchor)

With the defaults above, the expected active-region result is approximately:

- `VBB = 2.1053 V`, `RB = 8245.61 ohm`
- `IB = 0.0088 mA`, `IC = 1.3237 mA`, `IE = 1.3325 mA`
- `VB = 2.0325 V`, `VC = 5.7787 V`, `VE = 1.3325 V`, `VCE = 4.4462 V`
- Region: active

Both methods must agree on this case within `1e-6` relative.

### Testing

- `test_bjt_bias.py`: the worked example, an active case, a cutoff case
  (`VBB <= VBE`), a saturation case (`VCE < 0.2`), the near-threshold boundary
  cases (`VCE` just below, just above, and exactly at `0.2 V`), each validation
  rule, and non-numeric/`NaN` input.
- `test_independent.py`: both methods agree on a table of active, cutoff, and
  saturation cases, including boundary cases (`VBB == VBE`, and a deep
  saturation case where `VCE` is near zero); delta is within tolerance.
- `test_app.py`: `GET /` returns 200 and the prefilled form; valid `POST`
  returns 200 with values and "active"; invalid `POST` returns 200 with the
  error and no results table; values are preserved.
- Run with `python -m unittest discover -s tests -t .`.

### Delivery

1. Create `.venv`, install Flask, write `requirements.txt`.
2. Implement and test in TDD order.
3. Run the full suite and start the app on `127.0.0.1:5000` for a live check.
4. Commit to `main` with conventional messages (`docs:`, `feat:`, `test:`),
   matching existing history, and push to `origin`.
5. If the push prompts for credentials, stop and report rather than guessing.

## Decisions already made (not open)

- No clamping of cutoff/saturation values; warn instead.
- `RE > 0` is required, which also removes the nodal divide-by-zero case.
- `VCE(sat) = 0.2 V` is a constant.
- Currents are shown in mA; voltages in V; resistances in ohm.
- Cross-check compares raw `IC` and `VCE` from both methods.
- Comparison uses relative difference with `max(|a|, |b|)` as the denominator
  and an absolute floor of `1e-12` (A or V), so exact zeros are not false
  mismatches.
- Lab 2 delivery is the repo plus README only, with no Lab 1-style zip or
  evidence files, unless you tell me otherwise.

## Left to the builder

- Exact HTML structure and CSS styling within the constraints above.
- Wording of validation and region messages beyond the table's meaning.
- Which extra cases to add to the agreement table.
- Commit granularity and README prose.
