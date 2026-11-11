"""Flask web interface for the BJT common-emitter DC bias calculator.

This module owns the HTTP layer only. It reads the raw form strings, hands
them to `bjt_bias.parse_inputs` for validation, and hands validated inputs to
`bjt_bias.analyze` (Thevenin reduction) and `independent_check.solve` (direct
base-node KCL). Nothing here computes a voltage or a current.

One page does everything: `GET /` renders the form prefilled with a working
example, `POST /` validates, computes, and re-renders the same template with
either errors or results.
"""

from flask import Flask, render_template, request

from bjt_bias import BiasInputError, FIELDS, analyze, parse_inputs
from independent_check import compare, solve

__all__ = ["DEFAULTS", "app"]

# A working example: a 12 V stage biased into the active region.
DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}

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
    )


@app.route("/", methods=["GET", "POST"])
def index():
    """Show the form, or validate the submitted form and show the result."""
    if request.method == "GET":
        return _render(dict(DEFAULTS), {})

    # Keep every submitted value, including the invalid ones, so the user can
    # see what they typed and fix only the field that is wrong.
    values = {name: request.form.get(name, "") for name in FIELDS}

    try:
        inputs = parse_inputs(values)
    except BiasInputError as exc:
        return _render(values, exc.errors)

    result = analyze(inputs)
    independent = solve(inputs)
    comparison = compare(
        result.ic_ma, independent.ic_ma, result.vce_v, independent.vce_v
    )
    return _render(values, {}, result, independent, comparison)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
