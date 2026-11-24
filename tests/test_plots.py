import unittest

from plots import ac_plot, tran_plot, tran_window

AC_DATA = {
    "frequency_hz": [1.0, 10.0, 100.0],
    "gain_db": [-40.0, -35.0, -36.0],
    "phase_deg": [-170.0, -179.0, -180.0],
    "f_low_hz": 2.0,
    "f_high_hz": "not determined in sweep range",
}

TRAN_DATA = {
    "time_s": [i * 1e-4 for i in range(101)],
    "vin_v": [0.01] * 101,
    "vout_v": [-0.05] * 101,
    "frequency_hz": 10_000.0,
}


class TestPlots(unittest.TestCase):
    def test_tran_window_keeps_only_five_periods_of_real_samples(self):
        window = tran_window(TRAN_DATA)
        self.assertLess(len(window["time_s"]), len(TRAN_DATA["time_s"]))
        self.assertLessEqual(window["time_s"][-1], 5.0 / 10_000.0)
        self.assertEqual(window["vin_v"][0], TRAN_DATA["vin_v"][0])
        self.assertEqual(window["vout_v"][0], TRAN_DATA["vout_v"][0])

    def test_both_plots_are_png_data_uris_from_parsed_arrays(self):
        self.assertTrue(ac_plot(AC_DATA).startswith("data:image/png;base64,"))
        self.assertTrue(tran_plot(TRAN_DATA).startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
