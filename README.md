# BJT Common-Emitter DC Bias Calculator

Flask web app for the ENG29 2121 Lab 2 deliverable: enter the seven bias
values of an NPN common-emitter stage and get back the DC operating point —
with units, input validation, a region warning when the transistor is not in
the active region, and a second, independently coded calculation that is
compared against the first.

It is a bias calculator, not a circuit simulator. No AC, small-signal,
transient, or frequency analysis; no schematic editor or netlist; no FET or
MOSFET support; no database, login, or history.

## The circuit

```
        VCC
         |
    +----+----+
    |         |
   R1        RC
    |         |
    |         +--- C  (collector)
    +--- B    |
    |         +--- E  (emitter)
   R2         |
    |        RE
   GND        |
            GND
```

`B`, `C`, and `E` are the three terminals of the NPN transistor; the
transistor itself is the part joining them.

`VCC` feeds `R1` to the base and `RC` to the collector; `R2` runs from base to
ground; `RE` runs from emitter to ground. The transistor is modelled as a
fixed `VBE` drop and `IC = beta * IB`, which is valid in the active region.

## Inputs

All seven fields are required. Values are parsed as finite numbers; blank,
non-numeric, `NaN`, and infinite entries are rejected, and every bad field is
reported at once so they can all be fixed together.

| Field  | Symbol | Unit   | Rule                |
| ------ | ------ | ------ | ------------------- |
| `VCC`  | VCC    | volts  | greater than 0      |
| `R1`   | R1     | ohm    | greater than 0      |
| `R2`   | R2     | ohm    | greater than 0      |
| `RC`   | RC     | ohm    | greater than 0      |
| `RE`   | RE     | ohm    | greater than 0      |
| `beta` | beta   | —      | greater than 0      |
| `VBE`  | VBE    | volts  | `0 < VBE < VCC`      |

Invalid input never reaches the engineering code: the route validates first
and re-renders the form with the submitted values still in place.

## Outputs

| Quantity   | Meaning                          | Unit |
| ---------- | -------------------------------- | ---- |
| `VBB`      | Thevenin voltage of base divider | V    |
| `RB`       | Thevenin resistance of divider   | ohm  |
| `IB`       | base current                     | mA   |
| `IC`       | collector current                | mA   |
| `IE`       | emitter current                  | mA   |
| `VB`       | base voltage                     | V    |
| `VC`       | collector voltage                | V    |
| `VE`       | emitter voltage                  | V    |
| `VCE`      | collector-emitter voltage        | V    |

Currents are shown to four decimal places, voltages and resistances to three.

### Region

The linear solution is solved once and then classified:

| Condition        | Region      | Meaning                                              |
| ---------------- | ----------- | ---------------------------------------------------- |
| `VBB <= VBE`     | **cutoff**  | base-emitter junction not forward biased; transistor is off |
| `VCE < 0.2 V`    | **saturation** | below `VCE(sat)`; the active-region result is not the true operating point |
| otherwise        | **active**  | transistor is in the active region                    |

Nothing is clamped or silently replaced: outside the active region the numbers
are the raw solution of the same equations, and the page says so.

### Cross-check

Every result is computed twice. `bjt_bias.analyze` reduces the base divider to
its Thevenin equivalent and solves one base loop; `independent_check.solve`
writes Kirchhoff's current law straight into the base node instead. The two
paths share no algebra, so agreement between them is evidence that the
operating point is right. The page shows both values for `IC` and `VCE`, the
absolute and relative deltas, and a match indicator (relative difference
`<= 1e-6`, with an absolute floor so exact zeros are not false mismatches).

## Setup

Python 3.12 and a local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` requires Flask 3.x (`Flask>=3.0,<4.0`); it is the only
runtime dependency.

## Run

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

Then open <http://127.0.0.1:5000>.

The form arrives prefilled with a working example, so the first page load is
already demonstrable without typing anything. `POST /` validates, computes,
and re-renders the same page with either errors or results.

## Test

The full suite (model, cross-check, and web layer):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Lab 1's tests, which this work does not touch:

```powershell
.\.venv\Scripts\python.exe -m unittest test_electrical -v
```

## Worked example

The prefilled values:

| Input | Value    | Unit |
| ----- | -------- | ---- |
| VCC   | 12       | V    |
| R1    | 47000    | ohm  |
| R2    | 10000    | ohm  |
| RC    | 4700     | ohm  |
| RE    | 1000     | ohm  |
| beta  | 150      | —    |
| VBE   | 0.7      | V    |

give the active-region operating point:

| Quantity | Value      | Unit |
| -------- | ---------- | ---- |
| VBB      | 2.105      | V    |
| RB       | 8245.614   | ohm  |
| IB       | 0.0088     | mA   |
| **IC**   | **1.3237** | mA   |
| IE       | 1.3325     | mA   |
| VB       | 2.032      | V    |
| VC       | 5.779      | V    |
| VE       | 1.332      | V    |
| **VCE**  | **4.446**  | V    |

Region: **active**. The Thevenin and base-node KCL solves agree exactly here
(delta 0.0 for both `IC` and `VCE`).

## Files

```
app.py                   Flask app and routes only
bjt_bias.py              validation, Thevenin solve, region classification
independent_check.py     base-node KCL solve, no shared algebra
templates/index.html     the single page
static/style.css         layout and the region badge colours
tests/test_bjt_bias.py   model, regions, validation
tests/test_independent.py  agreement across cases
tests/test_app.py        GET, valid POST, invalid POST
requirements.txt         Flask 3.x (`>=3.0,<4.0`)
```

Lab 1 files (`electrical.py`, `test_electrical.py`) are untouched by this
project.

## Design notes

The full design and implementation plan live in `docs/superpowers/`:

- `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`
- `docs/superpowers/plans/2026-11-10-bjt-ce-bias.md`
