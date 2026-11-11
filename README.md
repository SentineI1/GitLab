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

`VCC` feeds `R1` to the base and `RC` to the collector; `R2` runs from base to
ground; `RE` runs from emitter to ground. The transistor is modelled as a fixed
`VBE` drop and `IC = beta * IB`, which is valid in the active region.

## Inputs

All seven fields are required. Values are parsed as finite numbers; blank,
non-numeric, `NaN`, and infinite entries are rejected, and every bad field is
reported at once so they can all be fixed together.

| Field  | Unit  | Rule             |
| ------ | ----- | ---------------- |
| `VCC`  | volts | greater than 0   |
| `R1`   | ohm   | greater than 0   |
| `R2`   | ohm   | greater than 0   |
| `RC`   | ohm   | greater than 0   |
| `RE`   | ohm   | greater than 0   |
| `beta` | —     | greater than 0   |
| `VBE`  | volts | `0 < VBE < VCC`  |

Invalid input never reaches the engineering code: the route validates first and
re-renders the form with the submitted values still in place.

## Outputs

| Quantity | Meaning                          | Unit | Digits |
| -------- | -------------------------------- | ---- | ------ |
| `VBB`    | Thevenin voltage of base divider | V    | 3      |
| `RB`     | Thevenin resistance of divider   | ohm  | 3      |
| `IB`     | base current                     | mA   | 4      |
| `IC`     | collector current                | mA   | 4      |
| `IE`     | emitter current                  | mA   | 4      |
| `VB`     | base voltage                     | V    | 3      |
| `VC`     | collector voltage                | V    | 3      |
| `VE`     | emitter voltage                  | V    | 3      |
| `VCE`    | collector-emitter voltage        | V    | 3      |

### Region

| Condition      | Region         | Meaning                                                      |
| -------------- | -------------- | ------------------------------------------------------------ |
| `VBB <= VBE`   | **cutoff**     | base-emitter junction not forward biased; transistor is off   |
| `VCE < 0.2 V`  | **saturation** | below `VCE(sat)`; the active-region result is not the true point |
| otherwise      | **active**     | transistor is in the active region                            |

Nothing is clamped: outside the active region the numbers are the raw solution
of the same equations, and the page says so.

### Cross-check

Every result is computed twice. `bjt_bias.analyze` reduces the base divider to
its Thevenin equivalent and solves one base loop; `independent_check.solve`
writes Kirchhoff's current law straight into the base node instead. The two
paths share no algebra. The page shows both values for `IC` and `VCE`, the
absolute and relative deltas, and a match indicator (relative difference
`<= 1e-6`, with an absolute floor so exact zeros are not false mismatches).

## Setup

Python 3.12 is installed at
`%LOCALAPPDATA%\Programs\Python\Python312\python.exe` on the lab machine:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` requires Flask 3.x (`Flask>=3.0,<4.0`); it is the only
runtime dependency.

## Run

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

Then open <http://127.0.0.1:5000>. The form arrives prefilled with the worked
example below, so the first page load is already demonstrable.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

34 tests: the model and region cases, the cross-check agreement cases, and the
web layer.

## Worked example

| Input | Value | Unit |
| ----- | ----- | ---- |
| VCC   | 12    | V    |
| R1    | 47000 | ohm  |
| R2    | 10000 | ohm  |
| RC    | 4700  | ohm  |
| RE    | 1000  | ohm  |
| beta  | 150   | —    |
| VBE   | 0.7   | V    |

gives the active-region operating point:

| Quantity   | Value     | Unit |
| ---------- | --------- | ---- |
| VBB        | 2.105     | V    |
| RB         | 8245.614  | ohm  |
| IB         | 0.0088    | mA   |
| **IC**     | **1.3237** | mA   |
| IE         | 1.3325    | mA   |
| VB         | 2.032     | V    |
| VC         | 5.779     | V    |
| VE         | 1.332     | V    |
| **VCE**    | **4.446** | V    |

Region: **active**. The Thevenin and base-node KCL solves agree exactly here
(delta 0.0 for both `IC` and `VCE`).

## Files

```
app.py                    Flask app and routes only
bjt_bias.py               validation, Thevenin solve, region classification
independent_check.py      base-node KCL solve, no shared algebra
templates/index.html      circuit diagram, form, results, and cross-check
static/style.css          layout and the region badge colours
tests/test_bjt_bias.py    model, regions, validation
tests/test_independent.py agreement across cases
tests/test_app.py         GET, valid POST, invalid POST, styling
requirements.txt          Flask 3.x
```

## Design notes

- `docs/superpowers/specs/2026-11-11-bjt-ce-bias-design.md`
- `docs/superpowers/plans/2026-11-11-bjt-ce-bias.md`
