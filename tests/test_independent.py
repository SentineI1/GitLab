import unittest

from bjt_bias import analyze, parse_inputs
from independent_check import compare, solve

CASES = {
    "active": {
        "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
    "cutoff": {
        "vcc": "12", "r1": "100000", "r2": "1000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
    "saturation": {
        "vcc": "5", "r1": "10000", "r2": "10000", "rc": "1000",
        "re": "100", "beta": "300", "vbe": "0.7",
    },
    "boundary_vbb_equals_vbe": {
        "vcc": "7", "r1": "9000", "r2": "1000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    },
}


class TestIndependentAgreement(unittest.TestCase):
    def test_methods_agree_across_cases(self):
        for name, form in CASES.items():
            with self.subTest(case=name):
                inputs = parse_inputs(form)
                main = analyze(inputs)
                other = solve(inputs)
                comparison = compare(
                    main.ic_ma, other.ic_ma, main.vce_v, other.vce_v
                )
                self.assertTrue(comparison.ic_match, f"IC mismatch in {name}")
                self.assertTrue(comparison.vce_match, f"VCE mismatch in {name}")
                self.assertLessEqual(comparison.ic_relative, 1e-6)
                self.assertLessEqual(comparison.vce_relative, 1e-6)


class TestCompare(unittest.TestCase):
    def test_exact_zeros_match(self):
        comparison = compare(0.0, 1e-12, 0.0, 1e-13)
        self.assertTrue(comparison.ic_match)
        self.assertTrue(comparison.vce_match)

    def test_real_difference_does_not_match(self):
        comparison = compare(1.0, 2.0, 1.0, 1.0)
        self.assertFalse(comparison.ic_match)
        self.assertAlmostEqual(comparison.ic_relative, 0.5)


if __name__ == "__main__":
    unittest.main()
