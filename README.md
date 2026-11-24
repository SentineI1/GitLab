# BJT Common-Emitter Bias Calculator + SPICE Lab

Flask web app for ENG29 2121. The original Lab 3 DC bias calculator is unchanged:
enter the seven bias values of an NPN common-emitter stage and get the operating
point with units, input validation, a region warning, and an independent
cross-check.

Lab 4 v1 adds **real** ngspice analysis for one reference voltage-divider
amplifier: `.op`, `.ac` and `.tran` runs with data-driven plots, the netlist and
the engine log, shown beside the analytical reference. No value in a SPICE
table or plot is invented; engine failures are displayed, never hidden.

Out of scope: emitter bypass variants, animated overlays, SPICE for the fixed
and emitter bias modes, a schematic/netlist editor, FET/MOSFET support, and any
database, login, or history.

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

The drawing beside the form follows the selected mode. Fixed bias shows `RB`
from `VCC` to the base, `RC` to the collector, and a grounded emitter; emitter
bias adds `RE` between emitter and ground. Labels show the values currently in
the form.

## Bias modes

Pick the network in the **Bias mode** selector. Only that mode's fields are
required; the others are ignored, so switching modes keeps the values you
already typed.

| Mode | Network | Fields used |
| ---- | ------- | ----------- |
| Voltage-divider bias | R1/R2 base divider, RC, RE | VCC, R1, R2, RC, RE, beta, VBE |
| Fixed bias | RB from VCC to base, RC to collector, emitter grounded | VCC, RB, RC, beta, VBE |
| Emitter bias | RB from VCC to base, RE to ground, RC to collector | VCC, RB, RC, RE, beta, VBE |

Fixed bias:

```
IB  = (VCC - VBE) / RB
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = 0
VB  = VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

Emitter bias:

```
IB  = (VCC - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

The divider keeps the Thevenin solve described below. Every mode returns the
same keys — `ib_ma`, `ic_ma`, `ie_ma` in mA; `vb_v`, `vc_v`, `ve_v`, `vce_v`
in V; plus `region` and `message` — so one results table serves all three.
The divider also reports `vbb_v` and `rb_ohm`.

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

## SPICE simulation (Lab 4 v1)

Choose **Voltage-divider bias**, select an analysis, then press **Run
Simulation**. The original **Calculate** button keeps the Lab 3 behaviour, and
fixed/emitter bias ignore the SPICE controls.

The reference circuit is fixed in `spice_engine.py`; only the source amplitude
and frequency fields are editable.

| Part | Value |
| ---- | ----- |
| VCC | 12 V |
| R1 / R2 | 100 kΩ / 22 kΩ |
| RC / RE | 2.2 kΩ / 1 kΩ |
| RL | 10 kΩ |
| Cin / Cout | 10 µF / 10 µF |
| Source | 10 mV peak, 1 kHz by default |

No instructor-verified starter files were present, so the netlist states its
own reproducible model:

```
.model CEQ NPN(IS=1E-14 BF=<beta from the form> VAF=100)
```

`BF` is the only link to the analytical beta field. `IS` and `VAF` are fixed,
documented constants; the analytical **VBE** field is *not* a SPICE parameter
(SPICE derives VBE from the model), which is why the two result blocks are not
expected to match digit-for-digit.

| Analysis | netlist command | Meaning |
| -------- | --------------- | ------- |
| DC | `.op` | VB, VE, VC, VCE and IC at the operating point |
| AC | `.ac dec 20 1 10Meg` | 141-point log sweep; gain is `20 log10 |V(output)/V(base)|` (Vin measured at the base after Cin), phase is the difference in degrees |
| Transient | `.tran 10u 5m 0 10u` at 1 kHz | Vin at the source side of Cin and Vout across RL; at higher frequencies the five-period stop and step both shrink, and the plot shows the first five periods of real samples |

A −3 dB cutoff is reported only when the real sweep crosses it; otherwise the
page shows the literal text `not determined in sweep range`. Node names in the
netlist are long (`base`, `collect`, `emit`, `output`) because single-letter
node names produce spurious `.print` parse warnings in this ngspice build.

## Setup

Python 3.12 is installed at
`%LOCALAPPDATA%\Programs\Python\Python312\python.exe` on the lab machine:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` requires Flask 3.x (`Flask>=3.0,<4.0`) and matplotlib
(`>=3.8`), which renders the SPICE plots.

SPICE needs the official ngspice-47 Windows 64-bit console binary. In this
workspace it is extracted to
`tools/ngspice/Spice64/bin/ngspice_con.exe` and gitignored; the binary is not
committed. `ngspice.exe` is silent in this environment and is deliberately not
used. To use another build, set `NGSPICE_PATH` to the executable — an invalid
explicit path fails fast instead of falling back silently.

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

70 tests: the original Lab 3 model/region/cross-check/web cases, the ngspice
netlist/parser/error-gate cases (including three real engine runs), the plot
window/PNG cases, and the SPICE web cases. The engine-dependent tests skip
themselves if no ngspice binary is available; the other SPICE form/error tests
still run.

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
bias_modes.py             mode list, per-mode validation, three solvers
bjt_bias.py               validation, Thevenin solve, region classification
independent_check.py      base-node KCL solve, no shared algebra
spice_engine.py           netlist, ngspice process, .print table parsing
plots.py                  matplotlib PNG data URIs from parsed arrays
templates/index.html      diagram, form, results, cross-check, SPICE panel
static/style.css          layout, badges, SPICE panel and plots
tests/test_bjt_bias.py    model, regions, validation
tests/test_independent.py agreement across cases
tests/test_app.py         GET/POST, styling, SPICE web cases
tests/test_spice_engine.py netlist, parsers, error gates, real ngspice smoke
requirements.txt          Flask 3.x and matplotlib 3.8+
AGENTS.md                 rules for AI contributors
docs/validation.md        real ngspice numbers and browser/HTTP verification
```

## Design notes

- `docs/superpowers/specs/2026-11-11-bjt-ce-bias-design.md`
- `docs/superpowers/plans/2026-11-11-bjt-ce-bias.md`
- `docs/superpowers/specs/2026-11-24-common-emitter-spice-v1-design.md`
- `docs/superpowers/plans/2026-11-24-common-emitter-spice-v1.md`
