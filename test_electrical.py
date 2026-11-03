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
        result = analyze_dc(12, series(4, 8))
        self.assertAlmostEqual(result["resistance_ohm"], 12.0)
        self.assertAlmostEqual(result["current_a"], 1.0)
        self.assertAlmostEqual(result["power_w"], 12.0)

    def test_parallel_circuit(self):
        result = analyze_dc(12, parallel(12, 12))
        self.assertAlmostEqual(result["resistance_ohm"], 6.0)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_mixed_circuit(self):
        circuit = series(6, parallel(12, 12))
        result = analyze_dc(12, circuit)
        self.assertAlmostEqual(result["resistance_ohm"], 12.0)
        self.assertAlmostEqual(result["current_a"], 1.0)
        self.assertAlmostEqual(result["power_w"], 12.0)

    def test_non_positive_resistance(self):
        for resistance in (0, -1):
            with self.subTest(resistance=resistance):
                with self.assertRaises(ValueError):
                    analyze_dc(12, resistance)


if __name__ == "__main__":
    unittest.main()