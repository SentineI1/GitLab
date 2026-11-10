import unittest

from bjt_bias import BiasInputError, parse_inputs

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


class TestParseInputs(unittest.TestCase):
    def test_parses_valid_form(self):
        inputs = parse_inputs(VALID)
        self.assertEqual(inputs.vcc_v, 12.0)
        self.assertEqual(inputs.r1_ohm, 47000.0)
        self.assertEqual(inputs.r2_ohm, 10000.0)
        self.assertEqual(inputs.rc_ohm, 4700.0)
        self.assertEqual(inputs.re_ohm, 1000.0)
        self.assertEqual(inputs.beta, 150.0)
        self.assertEqual(inputs.vbe_v, 0.7)

    def test_blank_field_is_reported(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "r1": "   "})
        self.assertEqual(ctx.exception.errors["r1"], "Enter a value.")

    def test_non_numeric_field_is_reported(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "rc": "abc"})
        self.assertEqual(ctx.exception.errors["rc"], "Enter a finite number.")

    def test_nan_and_inf_are_rejected(self):
        for bad in ("nan", "inf", "-inf"):
            with self.subTest(bad=bad):
                with self.assertRaises(BiasInputError) as ctx:
                    parse_inputs({**VALID, "beta": bad})
                self.assertIn("beta", ctx.exception.errors)

    def test_non_positive_resistances_are_rejected(self):
        for field, label in (("r1", "R1"), ("r2", "R2"), ("rc", "RC"), ("re", "RE")):
            for bad in ("0", "-5"):
                with self.subTest(field=field, bad=bad):
                    with self.assertRaises(BiasInputError) as ctx:
                        parse_inputs({**VALID, field: bad})
                    self.assertEqual(
                        ctx.exception.errors[field],
                        f"{label} must be greater than 0.",
                    )

    def test_vcc_must_be_positive(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "vcc": "0"})
        self.assertEqual(ctx.exception.errors["vcc"], "VCC must be greater than 0.")

    def test_beta_must_be_positive(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "beta": "-1"})
        self.assertEqual(ctx.exception.errors["beta"], "beta must be greater than 0.")

    def test_vbe_must_be_between_zero_and_vcc(self):
        for bad in ("0", "12", "13"):
            with self.subTest(bad=bad):
                with self.assertRaises(BiasInputError) as ctx:
                    parse_inputs({**VALID, "vbe": bad})
                self.assertIn("vbe", ctx.exception.errors)

    def test_collects_multiple_errors(self):
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs({**VALID, "vcc": "0", "beta": "-1"})
        self.assertGreaterEqual(len(ctx.exception.errors), 2)
        self.assertIn("vcc", ctx.exception.errors)
        self.assertIn("beta", ctx.exception.errors)


if __name__ == "__main__":
    unittest.main()
