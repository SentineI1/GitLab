"""Input validation for the BJT common-emitter DC bias calculator.

`parse_inputs` turns the raw form mapping submitted by the browser into a
validated `BiasInputs` record. Every bad field is reported in a single
`BiasInputError` so the user can fix them all at once.
"""

import math
from dataclasses import dataclass
from typing import Mapping

__all__ = ["BiasInputError", "BiasInputs", "parse_inputs"]

# Form field names, in the order they appear in the form.
FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

# Fields that must be strictly positive, with the label used in the message.
POSITIVE_FIELDS = (
    ("vcc", "VCC"),
    ("r1", "R1"),
    ("r2", "R2"),
    ("rc", "RC"),
    ("re", "RE"),
    ("beta", "beta"),
)

BLANK_MESSAGE = "Enter a value."
NUMBER_MESSAGE = "Enter a finite number."


class BiasInputError(ValueError):
    """Raised when one or more form fields fail validation.

    `errors` maps a form field name (`vcc`, `r1`, ...) to the message that
    belongs next to that field.
    """

    def __init__(self, errors: Mapping[str, str]) -> None:
        self.errors = dict(errors)
        super().__init__(
            "; ".join(f"{name}: {message}" for name, message in self.errors.items())
        )


@dataclass(frozen=True)
class BiasInputs:
    """Validated circuit inputs, in SI units (volts, ohms)."""

    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


def _parse_field(raw: object) -> tuple[float | None, str | None]:
    """Return (number, error message) for one submitted field value.

    The number is None when the field is blank, not a number, or not finite.
    """
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None, BLANK_MESSAGE
    try:
        number = float(text)
    except ValueError:
        return None, NUMBER_MESSAGE
    if not math.isfinite(number):
        return None, NUMBER_MESSAGE
    return number, None


def parse_inputs(form: Mapping[str, str]) -> BiasInputs:
    """Validate a submitted form and return the parsed inputs.

    Raises `BiasInputError` holding one message per invalid field.
    """
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for name in FIELDS:
        number, message = _parse_field(form.get(name))
        if message is not None:
            errors[name] = message
        else:
            values[name] = number

    for name, label in POSITIVE_FIELDS:
        number = values.get(name)
        if number is not None and number <= 0:
            errors[name] = f"{label} must be greater than 0."

    vbe = values.get("vbe")
    if vbe is not None:
        if vbe <= 0:
            errors["vbe"] = "VBE must be greater than 0."
        else:
            # The upper bound is only meaningful once VCC has parsed.
            vcc = values.get("vcc")
            if vcc is not None and vbe >= vcc:
                errors["vbe"] = "VBE must be less than VCC."

    if errors:
        raise BiasInputError(errors)

    return BiasInputs(
        vcc_v=values["vcc"],
        r1_ohm=values["r1"],
        r2_ohm=values["r2"],
        rc_ohm=values["rc"],
        re_ohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )
