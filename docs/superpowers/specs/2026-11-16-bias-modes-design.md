# Bias modes: divider, fixed, emitter

**Date:** 2026-11-16
**Status:** Approved — user confirmed the plan and formulas.

## Intent

Let the same page solve three single-supply bias networks: the existing
voltage-divider bias, fixed bias, and emitter bias. The divider result must
stay byte-for-byte the same as today, and the existing 43 tests must keep
passing without modification.

## Goals

- A `mode` selector with `divider`, `fixed`, `emitter`.
- Each mode validates only its own fields.
- Equations live in Python and return a plain `dict` whose keys carry units.
- Same key means the same quantity in every mode.
- No new `unittest` tests; verification is a Browser pass against the user's
  table.

## Non-goals

- Dual supplies, AC analysis, or extra components.
- A schematic drawing for the fixed and emitter modes (the divider drawing is
  shown only in divider mode, so the page never shows a circuit that does not
  match the result).
- Changing `bjt_bias.py`, `independent_check.py`, or `tests/`.

## Design

- New `bias_modes.py` owns the mode list, per-mode fields, per-mode
  validation, the three solvers, and the dispatcher.
- `solve_divider()` calls `bjt_bias.analyze()` and copies its fields into a
  dict, so the divider numbers are produced by exactly the same code path.
- `solve_fixed()` and `solve_emitter()` implement the lab-sheet equations.
- `parse_for_mode()` reuses `bjt_bias._parse_field` for the number parsing and
  repeats the existing positivity / `VBE < VCC` rules for the new modes.
- Result dict keys: `mode`, `ib_ma`, `ic_ma`, `ie_ma`, `vb_v`, `vc_v`,
  `ve_v`, `vce_v`, `region`, `message`; divider adds `vbb_v` and `rb_ohm`.
- `app.py` reads `mode`, validates per mode, dispatches, and runs the
  cross-check only for divider.
- The template always renders every input (so switching modes keeps the
  common values); fields the selected mode does not use are ignored by
  validation and labelled with their mode. VBB/RB rows and the divider
  schematic are conditional.
- `static/style.css` gains a full-width field, a `select` style, and a
  single-column workspace when the schematic is absent.

## Formulas

Fixed bias (`RB` from VCC to base, `RC` to collector, emitter grounded):

```
IB  = (VCC - VBE) / RB
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = 0
VB  = VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

Emitter bias (`RB` from VCC to base, `RE` from emitter to ground, `RC` to
collector):

```
IB  = (VCC - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

Divider: unchanged (`bjt_bias.analyze`).

Region: `VCE < 0.2 V` is saturation; `IB <= 0` is cutoff; otherwise active.
`VBE < VCC` is enforced by validation, so fixed/emitter normally cannot reach
cutoff.

## Unit conversion

Inputs arrive as volts and ohms. Currents are computed in amperes and
multiplied by `1000` once, at the point they enter the result dict. Voltages
stay in volts.

## Verification

- `python -m unittest discover -s tests -t .` → 43 tests OK, unchanged.
- Browser: `GET /` in divider mode; `POST /` with `mode=divider`, `fixed`,
  `emitter`, checked against the user's table.
