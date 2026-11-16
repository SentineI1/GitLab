"""Flask web interface for the BJT common-emitter DC bias calculator.

This module owns the HTTP layer only. It reads the raw form strings, hands
them to `bias_modes.parse_for_mode` for per-mode validation, and hands the
validated values to `bias_modes.solve`. Nothing here computes a voltage or a
current.

One page does everything: `GET /` renders the form prefilled with a working
divider example, `POST /` validates, computes, and re-renders the same
template with either errors or results. The `mode` field selects the bias
network; the divider mode additionally runs the independent cross-check.
"""

from flask import Flask, render_template, request

from bias_modes import MODES, MODE_LABELS, parse_for_mode, solve
from bjt_bias import BiasInputError, BiasInputs
from independent_check import compare, solve as solve_independent

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
}

# Every field the page can submit. Modes ignore the ones they do not use.
ALL_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe")

app = Flask(__name__)


def _render(values, errors, result=None, independent=None, comparison=None):
    """Render the page with the given context."""
    return render_template(
        "index.html",
        values=values,
        errors=errors,
        result=result,
        independent=independent,
        comparison=comparison,
        mode_labels=MODE_LABELS,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    """Show the form, or validate the submitted form and show the result."""
    if request.method == "GET":
        return _render(dict(DEFAULTS), {})

    mode = request.form.get("mode", "divider")
    if mode not in MODES:
        mode = "divider"

    # Keep every submitted value, including the invalid ones, so the user can
    # see what they typed and fix only the field that is wrong.
    values = {name: request.form.get(name, "") for name in ALL_FIELDS}
    values["mode"] = mode

    try:
        parsed = parse_for_mode(mode, values)
    except BiasInputError as exc:
        return _render(values, exc.errors)

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

    return _render(values, {}, result, independent, comparison)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
