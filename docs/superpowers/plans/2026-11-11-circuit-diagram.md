# Circuit Diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a drawn schematic of the NPN common-emitter bias stage to the bias page, showing the values typed into the form and the calculated region.

**Architecture:** One hand-written inline SVG in the existing template, beside the form in a two-column workspace. No new files, no JavaScript, no dependencies. Values bind through the existing Jinja `values` dict; the region pill reuses the existing badge classes and `result`.

**Tech Stack:** Flask 3.1 / Jinja2 / plain CSS / Python `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-circuit-diagram-design.md`

## Global Constraints

- No JavaScript and no new runtime dependency.
- No new files: the diagram lives in `templates/index.html`, styled from `static/style.css`.
- The diagram must render on `GET`, on a valid `POST`, on an invalid `POST`, and on a blank `POST`.
- The region pill appears only when `result` exists, and its class matches `result.region`.
- All existing tests keep passing (35 before this work).

## Review Focus

1. **Blank form POST** — the diagram still renders and shows no region pill.
2. **Invalid values** — the diagram shows the submitted string (e.g. `0 V`), not the previous/default value.
3. **Cutoff and saturation** — the pill follows `result.region`, not a hard-coded `active`.
4. **Huge or long values** — a long value may overflow the SVG text box; it must not break rendering or raise.
5. **No JavaScript** — the whole picture is in the server-rendered HTML.

---

### Task 1: Draw the circuit on the page

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `values: dict[str, str]` and `result: BiasResult | None` from `app.py`; badge classes `.badge-active`, `.badge-cutoff`, `.badge-saturation` from `static/style.css`.
- Produces: markup hooks `class="circuit"`, `<title id="circuit-title">`, `class="circuit-panel"`, `class="circuit-caption"`, and `class="circuit-region badge badge-<region>"`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_app.py`, before `if __name__ == "__main__":`:

```python
    def test_circuit_diagram_is_rendered(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertIn('role="img"', body)
        self.assertIn("circuit-title", body)
        for ref in ("VCC", "R1", "R2", "RC", "RE", "Q1"):
            self.assertIn(ref, body)

    def test_circuit_diagram_shows_default_values(self):
        body = self.client.get("/").get_data(as_text=True)
        for text in ("12 V", "47000 ohm", "10000 ohm", "4700 ohm", "1000 ohm"):
            self.assertIn(text, body)

    def test_circuit_diagram_reflects_submitted_value(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": "5"}).get_data(as_text=True)
        self.assertIn("5 V", body)
        self.assertNotIn("12 V", body)

    def test_circuit_diagram_shows_region_after_calculation(self):
        body = self.client.post("/", data=DEFAULTS).get_data(as_text=True)
        self.assertIn("circuit-region badge badge-active", body)

    def test_circuit_diagram_region_follows_cutoff(self):
        data = {**DEFAULTS, "r1": "100000", "r2": "1000"}
        body = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("circuit-region badge badge-cutoff", body)

    def test_circuit_diagram_survives_validation_errors(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": "0"}).get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertIn("0 V", body)
        self.assertNotIn("circuit-region", body)

    def test_circuit_diagram_on_blank_form(self):
        body = self.client.post("/", data={}).get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertNotIn("circuit-region", body)

    def test_circuit_diagram_handles_huge_values(self):
        response = self.client.post("/", data={**DEFAULTS, "vcc": "1000000"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("1000000 V", body)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`

Expected: 8 failures — `class="circuit"` and the other hooks are not in the page yet.

- [ ] **Step 3: Add the diagram to `templates/index.html`**

Wrap the form and a new `<figure>` in `<div class="workspace">`. Insert the figure before the form:

```html
  <div class="workspace">
    <figure class="circuit-panel">
      <svg class="circuit" viewBox="0 0 420 360" role="img" aria-labelledby="circuit-title">
        <title id="circuit-title">NPN common-emitter bias circuit: VCC feeds R1 and RC; R2 and RE return to ground.</title>
        <g class="wire">
          <path d="M120 30 H295"/>
          <path d="M120 30 V60"/>
          <path d="M120 105 V150"/>
          <path d="M120 150 H250"/>
          <path d="M120 150 V195"/>
          <path d="M120 240 V300"/>
          <path d="M295 30 V35"/>
          <path d="M295 70 V105"/>
          <path d="M250 140 L295 105"/>
          <path d="M250 160 L295 195"/>
          <path d="M295 195 V210"/>
          <path d="M295 255 V300"/>
          <path d="M120 300 H295"/>
          <path d="M210 300 V312"/>
          <path d="M200 312 H220"/>
          <path d="M205 317 H215"/>
          <path d="M208 322 H212"/>
        </g>
        <circle class="node" cx="120" cy="150" r="3.5"/>
        <line class="component" x1="250" y1="125" x2="250" y2="175"/>
        <polygon class="node" points="279,183 292,190 283,196"/>
        <rect class="component" x="112" y="60" width="16" height="45" rx="1"/>
        <rect class="component" x="112" y="195" width="16" height="45" rx="1"/>
        <rect class="component" x="287" y="35" width="16" height="35" rx="1"/>
        <rect class="component" x="287" y="210" width="16" height="45" rx="1"/>
        <text class="ref" x="120" y="20">VCC</text>
        <text class="val" x="152" y="20">{{ values.vcc }} V</text>
        <text class="ref" x="134" y="80">R1</text>
        <text class="val" x="134" y="96">{{ values.r1 }} ohm</text>
        <text class="ref" x="134" y="215">R2</text>
        <text class="val" x="134" y="231">{{ values.r2 }} ohm</text>
        <text class="ref" x="309" y="48">RC</text>
        <text class="val" x="309" y="64">{{ values.rc }} ohm</text>
        <text class="ref" x="309" y="226">RE</text>
        <text class="val" x="309" y="242">{{ values.re }} ohm</text>
        <text class="ref" x="302" y="160">Q1</text>
      </svg>
      <figcaption class="circuit-caption">
        <span>beta = {{ values.beta or "—" }} &middot; VBE = {{ values.vbe or "—" }} V</span>
        {% if result %}
        <span class="circuit-region badge badge-{{ result.region }}">{{ result.region|capitalize }}</span>
        {% endif %}
      </figcaption>
    </figure>

    <form method="post" action="/">
      ...
    </form>
  </div>
```

The existing `<form>` keeps its contents unchanged; only the opening `<form>` and closing `</form>` move inside the wrapper.

- [ ] **Step 4: Add the styles to `static/style.css`**

Change `.container`'s `max-width` to `880px`, then add:

```css
.workspace {
  display: grid;
  gap: 1.5rem;
  margin: 1.5rem 0;
  align-items: start;
}

@media (min-width: 760px) {
  .workspace { grid-template-columns: 1fr 1fr; }
}

.circuit-panel {
  margin: 0;
  padding: .75rem .75rem .5rem;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.circuit { display: block; width: 100%; height: auto; }

.circuit .wire { fill: none; stroke: currentColor; stroke-width: 2; }
.circuit .component { fill: #fff; stroke: currentColor; stroke-width: 2; }
.circuit .node { fill: currentColor; }
.circuit text { font-family: inherit; }
.circuit .ref { font-size: 12px; font-weight: 600; fill: var(--ink); }
.circuit .val { font-size: 11px; fill: var(--muted); }

.circuit-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .5rem;
  margin: .5rem 0 0;
  font-size: .85rem;
  color: var(--muted);
}

.workspace form { margin: 0; }
```

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`

Expected: all web tests pass (23 total: 15 existing + 8 new).

- [ ] **Step 6: Run the full suite**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`

Expected: `Ran 43 tests ... OK`.

- [ ] **Step 7: Commit**

```powershell
git add templates/index.html static/style.css tests/test_app.py
git commit -m "feat: draw the bias circuit beside the form"
```

---

### Task 2: Document and verify the live page

**Files:**
- Modify: `README.md` (Files section, one line)

**Interfaces:**
- Consumes: everything from Task 1.
- Produces: a README that mentions the diagram; a verified live page; the pushed commit.

- [ ] **Step 1: Update the README**

In the Files block, change the `templates/index.html` line to:

```text
templates/index.html      circuit diagram, form, results, and cross-check
```

- [ ] **Step 2: Run the full suite again**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`

Expected: `Ran 43 tests ... OK`.

- [ ] **Step 3: Start the server and verify the live page**

Run: `.\.venv\Scripts\python.exe -m flask --app app run --port 5000`

Then:

```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing).StatusCode
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Post -Body @{vcc="12";r1="47000";r2="10000";rc="4700";re="1000";beta="150";vbe="0.7"} -UseBasicParsing).Content | Select-String "class=.circuit.|47000 ohm|circuit-region badge badge-active"
```

Expected: `200`, then all three patterns found.

- [ ] **Step 4: Commit and push**

```powershell
git add README.md
git commit -m "docs: mention the circuit diagram"
$env:GIT_TERMINAL_PROMPT="0"
git push origin main
```

Expected: push accepted, `git log --oneline -1 origin/main` shows the Task 1 commit or later.
