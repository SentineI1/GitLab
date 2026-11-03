import unittest
from electrical import analyze_dc, parallel, series


class TestDCAnalyzer(unittest.TestCase):
    def test_known_values(self):
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_zero_voltage(self):
        result = analyze_dc(0, 10)
        self.assertAlmostEqual(result["current_a"], 0.0)
        self.assertAlmostEqual(result["power_w"], 0.0)

    def test_series_circuit(self):
        result = analyze_dc(12, series(3, 3))
        self.assertAlmostEqual(result["resistance_ohm"], 6.0)
        self.assertAlmostEqual(result["current_a"], 2.0)

    def test_parallel_circuit(self):
        result = analyze_dc(12, parallel(12, 12))
        self.assertAlmostEqual(result["resistance_ohm"], 6.0)
        self.assertAlmostEqual(result["current_a"], 2.0)

    def test_mixed_circuit(self):
        result = analyze_dc(12, series(6, parallel(12, 12)))
        self.assertAlmostEqual(result["resistance_ohm"], 12.0)
        self.assertAlmostEqual(result["current_a"], 1.0)
        self.assertAlmostEqual(result["power_w"], 12.0)

    def test_zero_resistance_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, 0)

    def test_negative_resistance_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, -5)


if __name__ == "__main__":
    unittest.main()