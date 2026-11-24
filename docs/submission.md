# Lab 4 submission notes — CE Amplifier Simulator

## Repository and commits

- Repository: <https://github.com/SentineI1/GitLab>
- Branch: `main`
- Lab 4 ngspice adapter: `402217ec17f4f35cda1c67f1074d3dbd0209a6f4`
- Lab 4 web SPICE runs and plots: `8b6307893c88045aed2da1347c9dd0c97396d8d5`
- UI review/polish: `51b14b146edebfddfa4326a4ca65daf20f9f502e`
- Final documentation/evidence commit: read with `git rev-parse HEAD` after push
  (the Lab 4 code SHA above is already fixed and pushed).

## Submission checklist mapping

| Checklist item | Where it is satisfied |
| --- | --- |
| GitHub URL + Commit SHA for Lab 4 | This section; code SHAs are fixed, documentation commit from `git log -1` |
| Flask app with CE SPICE DC/AC/Transient and the 3 original DC Bias modes | `app.py`, `spice_engine.py`, `plots.py`, `templates/index.html`; 70 tests OK |
| README installation, ngspice, server and browser steps | [`README.md`](../README.md), sections “Setup”, “Run”, “SPICE simulation (Lab 4 v1)” |
| `docs/validation.md` records B1–B8, method, observed results, references, deviations and limits | [`docs/validation.md`](validation.md), section “Lab 4 — Browser acceptance B1–B8” |
| Before/after UI screenshots or Impeccable record, plus real-browser graph screenshots | [`ui-before-desktop-ac.png`](evidence/ui-before-desktop-ac.png) → [`ui-after-desktop-ac.png`](evidence/ui-after-desktop-ac.png), [`ui-before-mobile-ac.png`](evidence/ui-before-mobile-ac.png) → [`ui-after-mobile-ac.png`](evidence/ui-after-mobile-ac.png); B4/B5/B6 screenshots in [`docs/evidence/`](evidence/) |
| 3–5 lines recording AI work and student checks | “AI / student record” below |
| Short oral-check answers | “Short answers for individual checking” below |

Not committed: `.venv/`, `.env`, `tools/ngspice/` (the ngspice binary), API keys,
tokens and temporary Playwright scripts. `docs/evidence/` contains only selected
screenshots and the 25 KB `B1-B8-report.json`; the simulation can be regenerated
with the commands below.

## AI / student record

- **AI created:** the ngspice adapter (`spice_engine.py`), data-driven plots (`plots.py`), the SPICE panel in `app.py`/`templates/index.html`, and later UI polish (fieldsets, provenance chips, responsive plot scroll, error callouts).
- **AI recorded honestly:** Playwright MCP and the `impeccable` skill were not exposed in this harness; local Playwright + Chrome and before/after screenshots were used instead, and this is stated in `docs/validation.md`.
- **Student checked:** the analytical equations and units, the fixed model `.model CEQ NPN(IS=1E-14 BF=<beta> VAF=100)`, and the separation of analytical (fixed VBE, constant β) from SPICE (model-derived VBE).
- **Student checked in a real browser:** B1–B8 with fresh navigation, snapshots and real submits; compared netlists, ngspice log rows and plot hashes so the Bode/waveform traces are demonstrably not mock data.
- **Student checked failure paths:** RE = 0 and an explicitly invalid `NGSPICE_PATH`; both show visible errors with no success badge and no plot.

## Short answers for individual checking

**1. Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?**  
`spice_engine.py` builds a text netlist from the form values (`VCC`, `R1`, `R2`,
`RC`, `RE`, `beta`, amplitude, frequency) with `.op`, `.ac` or `.tran` plus the
matching `.print` lines. It runs `ngspice_con.exe` as a list-form subprocess with
a timeout (never `shell=True`), captures stdout/stderr, rejects nonzero exit
codes and `Error:`/`Fatal error:` text, then joins all pages of each `.print`
table and parses them into arrays used by the tables and plots. An explicit bad
`NGSPICE_PATH` fails fast with that path shown.

**2. เหตุใดกราฟ `.ac` และ `.tran` จึงไม่ใช่สิ่งเดียวกัน?**  
`.ac` is a small-signal frequency sweep: its x-axis is Hz (log sweep 1 Hz–10 MHz)
and its values are gain `20log10|V(output)/V(base)|` in dB plus phase in degrees
from `vp()`. `.tran` is a time-domain sine run: its x-axis is time with adaptive
ms/µs/ns units and it plots the actual `v(input)` and `v(output)` waveforms. They
answer different questions and come from different `.print` tables.

**3. ถ้าเปลี่ยน Amplitude แต่กราฟไม่เปลี่ยน คุณจะตรวจข้อมูลตรงไหนก่อน?**  
Check the netlist first: `Vs ... SIN(0 <amplitude> <frequency>)`. Then check the
ngspice `.print tran` rows for a changed peak |Vin|, and finally compare the
base64 PNG bytes/SHA256. In B6 the SIN line changed `0.01 → 0.02`, peaks roughly
doubled, and the PNG hash changed `316ac0ff… → 75256a27…`; if the netlist/log
change but the PNG does not, the fault is in `plots.py`, not the engine.

**4. Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?**  
It may change layout grouping, readability, legends/units, status chips, error
callouts and responsive behaviour. It must not change the equations, netlist,
parser, SPICE values, chart data, units, or hide engine errors to keep a plot on
screen. In this run the skill was unavailable; the same boundaries were kept
manually and before/after screenshots are provided.

**5. คุณรู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?**  
The page shows the exact netlist with `.ac dec 20 1 10Meg` and four
`.print ac vdb/vp(output/base)` lines, plus an ngspice log excerpt with real
numeric rows. The displayed 4.895 dB / 1.309769 Hz / `not determined in sweep
range` values match the recorded ngspice run, and changing RE changed both the
numbers and the PNG hash (`9a21d8… → 2f18ae…`). A hard-coded trace could not
respond to netlist changes.

## Rubric evidence map (10 points)

| Rubric item | Points | Evidence |
| --- | ---: | --- |
| Continuity from Lab 3 | 1 | B1 three-mode PASS in [`validation.md`](validation.md), original 43 tests still included in the 70-test run |
| ngspice connection | 3 | B2 PASS, netlist/log details, exit code 0, visible model; B7 failure gates; adapter tests |
| AC + Transient | 2 | B4, B5 and B6 PASS with real `.print` provenance, units and source response |
| UI and Impeccable | 2 | Before/after screenshots above; UI commit `51b14b1`; plot data unchanged |
| Browser acceptance | 1 | B1–B8 table and [`B1-B8-report.json`](evidence/B1-B8-report.json), with honest MCP/skill limitations |
| GitHub + reproducibility | 1 | This file, README setup/run/test commands, fixed code SHAs, selected evidence, no binaries committed |

## Reproduce locally

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install the ngspice-47 Windows 64-bit console build and either place
`ngspice_con.exe` at `tools/ngspice/Spice64/bin/ngspice_con.exe` or set
`NGSPICE_PATH` to it. Then:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 5000
```

Open <http://127.0.0.1:5000/>, type the fixture values from
[`validation.md`](validation.md), select an analysis and press **Run
Simulation**. Each result block includes the netlist and ngspice log excerpt.
Run the suite with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```
