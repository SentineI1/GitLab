import os
import unittest
from unittest.mock import patch

from spice_engine import (
    RunResult,
    SimulationError,
    build_netlist,
    check_run,
    cutoff_frequencies,
    parse_ac,
    parse_op,
    parse_tran,
    resolve_ngspice,
    simulate,
)

VALUES = {
    "vcc": 12.0,
    "r1": 100_000.0,
    "r2": 22_000.0,
    "rc": 2_200.0,
    "re": 1_000.0,
    "beta": 150.0,
    "amplitude_mv": 10.0,
    "frequency_hz": 1_000.0,
}

OP_TEXT = (
    "Index   v(base)         v(emit)         v(collect)      @q1[ic]         \n"
    "--------------------------------------------------------------------------------\n"
    "0\t2.013016e+00\t1.352006e+00\t9.044000e+00\t1.344126e-03\t\n"
)


def _ac_table(header, values):
    rows = "\n".join(
        f"{i}\t{f:.6e}\t{v:.6e}\t" for i, (f, v) in enumerate(values)
    )
    return f"Index   frequency       {header}\n" + "-" * 80 + "\n" + rows + "\n"


class TestNetlist(unittest.TestCase):
    def test_netlist_has_model_and_analysis(self):
        nl = build_netlist("ac", VALUES)
        self.assertIn(".model CEQ NPN(IS=1E-14 BF=150 VAF=100)", nl)
        self.assertIn(".ac dec 20 1 10Meg", nl)
        self.assertIn("Cin input base 10u", nl)
        self.assertIn("Cout collect output 10u", nl)
        self.assertIn("RL output 0 10k", nl)
        self.assertIn("Vs input 0 DC 0 AC 0.01 SIN(0 0.01 1000)", nl)
        self.assertIn(".print ac vdb(output)", nl)
        self.assertIn(".print ac vp(base)", nl)

    def test_op_and_tran_analysis_lines(self):
        self.assertIn(".op", build_netlist("dc", VALUES))
        self.assertIn(".tran 10u 5m 0 10u", build_netlist("tran", VALUES))


class TestEngineErrors(unittest.TestCase):
    def test_check_run_rejects_error_text_with_zero_exit(self):
        result = RunResult("dc", "", "Error: no data saved", 0, "fake")
        with self.assertRaises(SimulationError):
            check_run(result)

    def test_resolve_ngspice_reports_bad_env(self):
        with patch.dict(os.environ, {"NGSPICE_PATH": r"C:\does\not\exist\ngspice.exe"}):
            with self.assertRaises(SimulationError) as cm:
                resolve_ngspice()
        self.assertIn(r"does\not\exist", str(cm.exception))


class TestParsers(unittest.TestCase):
    def test_parse_op_reads_ngspice_table(self):
        data = parse_op(OP_TEXT)
        self.assertAlmostEqual(data["vb_v"], 2.013016, places=6)
        self.assertAlmostEqual(data["ic_ma"], 1.344126, places=6)
        self.assertAlmostEqual(data["vce_v"], 9.044 - 1.352006, places=6)

    def test_parse_ac_and_cutoff_reports_missing_crossing(self):
        frequencies = [(10.0, -43.0), (1000.0, -35.105), (100000.0, -43.0)]
        base = [(f, -40.0) for f, _ in frequencies]
        out_phase = [(10.0, -3.0), (1000.0, -3.14159), (100000.0, -3.0)]
        zero_phase = [(f, 0.0) for f, _ in frequencies]
        text = "\n".join(
            [
                _ac_table("vdb(output)     ", frequencies),
                _ac_table("vp(output)      ", out_phase),
                _ac_table("vdb(base)       ", base),
                _ac_table("vp(base)        ", zero_phase),
            ]
        )
        data = parse_ac(text)
        self.assertEqual(len(data["frequency_hz"]), 3)
        self.assertAlmostEqual(data["gain_db"][1], 4.895, delta=0.01)
        self.assertAlmostEqual(data["phase_deg"][1], -180.0, delta=1.0)
        self.assertEqual(cutoff_frequencies([10.0, 1000.0, 100000.0], [1.0, 1.0, 1.0]), (None, None))

    def test_parse_tran_reads_real_sample_count(self):
        text = (
            "Index   time            v(input)        v(output)       \n"
            "--------------------------------------------------------------------------------\n"
            "0\t0.000000e+00\t0.000000e+00\t0.000000e+00\t\n"
            "1\t1.000000e-05\t6.283185e-03\t-1.100000e-02\t\n"
            "2\t2.000000e-05\t1.256637e-02\t-2.200000e-02\t\n"
        )
        data = parse_tran(text)
        self.assertEqual(data["time_s"][0], 0.0)
        self.assertEqual(len(data["vin_v"]), 3)


class TestRealNgspice(unittest.TestCase):
    def test_real_ngspice_smoke(self):
        try:
            resolve_ngspice()
        except SimulationError as exc:
            self.skipTest(f"ngspice not available: {exc}")
        for analysis in ("dc", "ac", "tran"):
            with self.subTest(analysis=analysis):
                result = simulate(analysis, VALUES)
                self.assertEqual(result["status"], "success")
                self.assertTrue(result["netlist"])
                self.assertTrue(result["log"])
                if analysis == "dc":
                    self.assertGreater(result["data"]["vb_v"], 0.0)
                    self.assertGreater(result["data"]["ic_ma"], 0.0)
                else:
                    key = "frequency_hz" if analysis == "ac" else "time_s"
                    self.assertGreater(len(result["data"][key]), 0)


if __name__ == "__main__":
    unittest.main()
