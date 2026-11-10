import unittest

from bjt_bias import BiasInputError, VCE_SAT_V, analyze, parse_inputs

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


def make(**overrides):
    return parse_inputs({**VALID, **overrides})


class TestAnalyze(unittest.TestCase):
    def test_worked_example_is_active(self):
        result = analyze(make())
        self.assertEqual(result.region, "active")
        self.assertIn("active", result.message.lower())
        self.assertAlmostEqual(result.vbb_v, 2.1052632, delta=1e-6)
        self.assertAlmostEqual(result.rb_ohm, 8245.614035, delta=1e-3)
        self.assertAlmostEqual(result.ib_ma, 0.0088245, delta=1e-7)
        self.assertAlmostEqual(result.ic_ma, 1.3236752, delta=1e-6)
        self.assertAlmostEqual(result.ie_ma, 1.3324997, delta=1e-6)
        self.assertAlmostEqual(result.vb_v, 2.0324997, delta=1e-6)
        self.assertAlmostEqual(result.vc_v, 5.7787265, delta=1e-6)
        self.assertAlmostEqual(result.ve_v, 1.3324997, delta=1e-6)
        self.assertAlmostEqual(result.vce_v, 4.4462268, delta=1e-6)

    def test_cutoff_when_vbb_below_vbe(self):
        result = analyze(make(r1="100000", r2="1000"))
        self.assertEqual(result.region, "cutoff")
        self.assertIn("cutoff", result.message.lower())
        self.assertGreater(result.vce_v, VCE_SAT_V)

    def test_cutoff_boundary_has_zero_current(self):
        result = analyze(make(vcc="7", r1="9000", r2="1000"))
        self.assertEqual(result.region, "cutoff")
        self.assertAlmostEqual(result.ic_ma, 0.0, places=12)
        self.assertAlmostEqual(result.vce_v, 7.0, places=12)

    def test_saturation_when_vce_below_threshold(self):
        result = analyze(
            make(vcc="5", r1="10000", r2="10000", rc="1000", re="100", beta="300")
        )
        self.assertEqual(result.region, "saturation")
        self.assertIn("saturation", result.message.lower())
        self.assertLess(result.vce_v, VCE_SAT_V)


if __name__ == "__main__":
    unittest.main()
