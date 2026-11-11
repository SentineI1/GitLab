# BJT Common-Emitter DC Bias Web App — Design

- **Date:** 2026-11-11
- **Course:** ENG29 2121, Lab 2
- **Status:** Awaiting approval
- **Repo:** `SentineI1/GitLab`, branch `main`

## Intent

A small, working Flask app for the Lab 2 deliverable: enter the seven bias
values of an NPN common-emitter stage and read the DC operating point with
units, input validation, a region warning, and a second independently coded
calculation shown beside the first so the answer is not the artefact of one
equation path.

This is a rebuild, not a new idea. A complete version of this app exists in
commit `b9b6e8f` and was deleted in eight later commits. That version was
correct but oversized for a short lab: 2,039 lines, including a 274-line
stylesheet, a 213-line template, a 258-line design and a 567-line plan. This
design keeps the part that is hard to get right — the engineering core — and
replaces the presentation layer with something a lab report can carry.

## Goals

- Accept `VCC`, `R1`, `R2`, `RC`, `RE`, `beta`, `VBE` from one web form.
- Return `VBB`, `RB`, `IB`, `IC`, `IE`, `VB`, `VC`, `VE`, `VCE` with units.
- Classify the region as active, cutoff, or saturation and warn otherwise.
- Reject invalid input with a message per field, keeping what was typed.
- Cross-check the operating point (`IC` and `VCE`) with a second implementation
  and show the delta.
- Keep engineering logic, routes, template, CSS, and tests in separate files.
- Run on localhost and be committed to GitHub the same day.
- Leave a README that describes the code that actually exists.

## Non-goals

- No AC, small-signal, transient, or frequency analysis.
- No schematic editor, netlist, or arbitrary circuit solving.
- No FET/MOSFET support.
- No database, login, persistence, or history.
- No JavaScript framework, charting, or SPICE integration.

## Anti-goals

- A README that documents deleted files.
- Physics duplicated in the HTTP layer.
- Silent clamping when the transistor is saturated or cut off.
- A result that cannot be reproduced by hand.

## Constraints

- **Python is not installed on this machine.** Only the Windows Store stub
  exists; `py`, `npm`, `uv`, and `winget` are absent. Python 3.12 must be
  installed before anything can run. Plan: official python.org per-user silent
  install; fall back to the Store package if the installer is blocked.
- Flask 3.x is the only runtime dependency (`Flask>=3.0,<4.0`).
- Tests use the standard library `unittest`, matching Lab 1.
- Lab 1 files (`electrical.py`, `test_electrical.py`) must not be modified.
- Commits go directly to `main`, following the existing history.
- The working tree is clean at `ecb7008`; the deleted app is recoverable from
  `b9b6e8f`.

## Approaches considered

- **A — Restore the whole deleted version.** `git checkout b9b6e8f -- …`
  brings back all 2,039 lines and the old docs. Fastest, but it is exactly the
  size problem this rebuild exists to fix, and the stale plan and design come
  with it. Rejected.
- **B — Keep the engineering core, rewrite the web layer thin. (Chosen)**
  Restore `bjt_bias.py`, `independent_check.py`, and their two test modules
  verbatim. Write a new route module, template, stylesheet, web-layer tests,
  and README at roughly a third of the old size. Keeps the parts that are
  expensive to verify and discards the parts that only made the project look
  big.
- **C — Write everything from scratch.** Smallest possible result, but the
  equations, validation, and cross-check would be rewritten and re-verified
  under time pressure for no gain. Rejected.

## Design

### Files

```
app.py                    Flask app and the single route
bjt_bias.py               validation, Thevenin solve, region classification
independent_check.py      base-node KCL solve, no shared algebra
templates/index.html      the single page
static/style.css          layout and region badge colours
tests/__init__.py         makes `tests` importable for unittest discovery
tests/test_bjt_bias.py    model, regions, validation
tests/test_independent.py agreement across cases
tests/test_app.py         GET, valid POST, invalid POST
requirements.txt          Flask 3.x
README.md                 what the app is, how to run and test it
```

`bjt_bias.py`, `independent_check.py`, `tests/test_bjt_bias.py`, and
`tests/test_independent.py` are restored from `b9b6e8f` unchanged. Everything
else is written new and smaller.

### Behaviour

- `GET /` renders the form prefilled with the working example
  (`VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, beta=150, VBE=0.7`).
- `POST /` validates first, then computes, then re-renders the same page with
  either per-field errors or results. Invalid input never reaches the
  engineering code.
- Form field names are the lowercase symbols (`vcc`, `r1`, …). Units are fixed
  by the form: volts and ohms; `beta` is dimensionless.
- Display precision: currents to four decimals in mA, voltages and resistances
  to three.
- Region: `VBB <= VBE` → cutoff; else `VCE < 0.2 V` → saturation; else active.
  Nothing is clamped; the page states that the numbers are the raw solution.
- Cross-check: both solves run on every request; the page shows both `IC` and
  `VCE`, absolute and relative deltas, and a match indicator using the existing
  relative tolerance with absolute floors. The independent solver also produces
  `VB`, `VE`, and `VC`; those are computed but not displayed, to keep the page
  to one comparison table.

### Presentation decisions

- One server-rendered page, no JavaScript, no separate results page.
- Inputs stay in place after a validation error.
- Results are a labelled table with units plus a region badge; the cross-check
  sits under it.
- Styling is plain CSS, one small stylesheet, no framework.

### Left to the builder

- Exact markup, class names, and stylesheet rules.
- Wording of labels, hints, and the region and cross-check captions.
- Which extra cases the web-layer tests cover beyond GET, valid POST, and
  invalid POST.
- How Python is installed, as long as the app ends up runnable.

## Success criteria

- `python -m unittest discover -s tests -t .` passes.
- The prefilled example yields `IC = 1.3237 mA`, `VCE = 4.446 V`, region
  active, and the two methods agree.
- The app serves on `http://127.0.0.1:5000` and is demonstrated live.
- The README matches the files on disk.
- A clean series of commits on `main` (one per task) containing the design
  doc, the plan, and the rebuild, pushed to `origin/main`. If credentials or
  the network block the push, the commits still stand and the push is reported
  as the one open item.

## Risks

- Python installation may require network access or elevation. If it fails,
  the Store package is the fallback and the demo moves to that interpreter.
- The restored tests target the restored modules and are expected to pass
  unchanged; if the Python version differs, that is checked before the plan is
  executed.
