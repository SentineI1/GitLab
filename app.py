"""Flask web interface for the BJT common-emitter bias calculator and SPICE lab.

This module owns the HTTP layer only. It reads the raw form strings, hands
them to `bias_modes.parse_for_mode` for per-mode validation, and hands the
validated values to `bias_modes.solve`. Nothing here computes a voltage or a
current. For divider mode, an optional `action=simulate` additionally runs
`spice_engine.simulate` and renders its real output beside the analytical
reference; all other POSTs keep the original Lab 3 behaviour.
"""

from flask import Flask, render_template, request

from bias_modes import MODES, MODE_LABELS, parse_for_mode, solve
from bjt_bias import BiasInputError, BiasInputs, _parse_field
from independent_check import compare, solve as solve_independent
from plots import ac_plot, tran_plot
from spice_engine import SimulationError, build_netlist, simulate

__all__ = ["DEFAULTS", "app"]

# A working example: a 12 V stage biased into the active region. `rb` is the
# base resistor used by the fixed and emitter modes; the divider ignores it.
DEFAULTS = {
    "mode": "divider",
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rb": "1200000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
    # Source for the optional SPICE run: 10 mV peak at 1 kHz.
    "analysis": "dc",
    "amplitude_mv": "10",
    "frequency_hz": "1000",
}

# Every field the page can submit. Modes ignore the ones they do not use.
ALL_FIELDS = (
    "vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe",
    "analysis", "amplitude_mv", "frequency_hz",
)

SIM_ANALYSES = ("dc", "ac", "tran")
ANALYSIS_LABELS = {
    "dc": "DC operating point",
    "ac": "AC frequency response",
    "tran": "Transient waveform",
}

app = Flask(__name__)


def _render(values, errors, result=None, independent=None, comparison=None,
            sim=None, analysis=None, plot_ac=None, plot_tran=None):
    """Render the page with the given context."""
    return render_template(
        "index.html",
        values=values,
        errors=errors,
        result=result,
        independent=independent,
        comparison=comparison,
        sim=sim,
        analysis=analysis,
        analysis_labels=ANALYSIS_LABELS,
        plot_ac=plot_ac,
        plot_tran=plot_tran,
        mode_labels=MODE_LABELS,
    )


def _parse_sim_fields(form):
    """Validate the editable source fields before any netlist is built."""
    errors = {}
    values = {}
    for name, label in (("amplitude_mv", "Amplitude"),
                        ("frequency_hz", "Frequency")):
        number, message = _parse_field(form.get(name))
        if message is not None:
            errors[name] = message
        elif number <= 0:
            errors[name] = f"{label} must be greater than 0."
        elif name == "frequency_hz" and number > 1e9:
            errors[name] = "Frequency must be at most 1 GHz."
        else:
            values[name] = number
    if errors:
        raise BiasInputError(errors)
    return values


@app.route("/", methods=["GET", "POST"])
def index():
    """Show the form, or validate the submitted form and show the result."""
    if request.method == "GET":
        return _render(dict(DEFAULTS), {})

    mode = request.form.get("mode", "divider")
    if mode not in MODES:
        mode = "divider"

    analysis = request.form.get("analysis", "dc")
    # SPICE is additive: a simulate request for any other bias mode is ignored
    # and the ordinary analytical Lab 3 result is shown.
    sim_requested = request.form.get("action") == "simulate" and mode == "divider"

    # Keep every submitted value, including the invalid ones, so the user can
    # see what they typed and fix only the field that is wrong.
    values = {name: request.form.get(name, "") for name in ALL_FIELDS}
    values["mode"] = mode
    values["analysis"] = analysis

    if sim_requested and analysis not in SIM_ANALYSES:
        return _render(values, {"analysis": "Choose DC, AC, or Transient."},
                       analysis=analysis)

    try:
        parsed = parse_for_mode(mode, values)
        sim_values = _parse_sim_fields(values) if sim_requested else None
    except BiasInputError as exc:
        return _render(values, exc.errors, analysis=analysis)

    result = solve(mode, parsed)

    independent = None
    comparison = None
    if mode == "divider":
        inputs = BiasInputs(
            vcc_v=parsed["vcc"],
            r1_ohm=parsed["r1"],
            r2_ohm=parsed["r2"],
            rc_ohm=parsed["rc"],
            re_ohm=parsed["re"],
            beta=parsed["beta"],
            vbe_v=parsed["vbe"],
        )
        independent = solve_independent(inputs)
        comparison = compare(
            result["ic_ma"], independent.ic_ma, result["vce_v"], independent.vce_v
        )

    sim = plot_ac = plot_tran = None
    if sim_requested:
        engine_values = {**parsed, **sim_values}
        try:
            sim = simulate(analysis, engine_values)
        except SimulationError as exc:
            # Never hide an engine failure: keep its message, raw detail and
            # the exact netlist that would have been run.
            sim = {
                "status": "error",
                "analysis": analysis,
                "message": str(exc),
                "detail": exc.detail,
                "netlist": build_netlist(analysis, engine_values),
                "log": "",
            }
        else:
            sim["log_excerpt"] = sim["log"][-1500:]
            if analysis == "ac":
                plot_ac = ac_plot(sim["data"])
            elif analysis == "tran":
                plot_tran = tran_plot(sim["data"])

    return _render(values, {}, result, independent, comparison,
                   sim=sim, analysis=analysis, plot_ac=plot_ac, plot_tran=plot_tran)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
