import os
import unittest
from unittest.mock import patch

from app import DEFAULTS, app
from spice_engine import SimulationError, resolve_ngspice


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_shows_prefilled_form(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="vcc"', body)
        self.assertIn('value="12"', body)
        self.assertNotIn("DC Operating Point", body)

    def test_valid_post_shows_operating_point(self):
        response = self.client.post("/", data=DEFAULTS)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("DC Operating Point", body)
        self.assertIn("Active", body)
        self.assertIn("1.3237", body)
        self.assertIn("4.446", body)
        self.assertIn("Thevenin", body)
        self.assertIn("Nodal", body)

    def test_saturation_post_shows_warning(self):
        data = {**DEFAULTS, "vcc": "5", "r1": "10000", "r2": "10000",
                "rc": "1000", "re": "100", "beta": "300"}
        body = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("DC Operating Point", body)

    def test_cutoff_post_shows_warning(self):
        data = {**DEFAULTS, "r1": "100000", "r2": "1000"}
        body = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("DC Operating Point", body)

    def test_tiny_beta_still_renders(self):
        body = self.client.post("/", data={**DEFAULTS, "beta": "1"}).get_data(as_text=True)
        self.assertIn("DC Operating Point", body)
        self.assertNotIn("nan", body.lower())

    def test_huge_magnitudes_still_render(self):
        data = {**DEFAULTS, "vcc": "1000000", "r1": "1", "r2": "1",
                "rc": "1", "re": "1"}
        response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("DC Operating Point", body)
        self.assertNotIn("nan", body.lower())

    def test_invalid_post_shows_error_and_preserves_values(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": "0"}).get_data(as_text=True)
        self.assertNotIn("DC Operating Point", body)
        self.assertIn("greater than 0", body)
        self.assertIn('value="47000"', body)

    def test_blank_form_reports_every_field(self):
        body = self.client.post("/", data={}).get_data(as_text=True)
        self.assertEqual(body.count("Enter a value."), 7)
        self.assertNotIn("DC Operating Point", body)

    def test_vbe_must_be_below_vcc(self):
        body = self.client.post("/", data={**DEFAULTS, "vbe": "12"}).get_data(as_text=True)
        self.assertIn("VBE must be less than VCC.", body)
        self.assertNotIn("DC Operating Point", body)

    def test_overflow_text_is_rejected(self):
        body = self.client.post("/", data={**DEFAULTS, "r1": "1e400"}).get_data(as_text=True)
        self.assertIn("Enter a finite number.", body)
        self.assertNotIn("DC Operating Point", body)

    def test_whitespace_is_accepted(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": " 12 "}).get_data(as_text=True)
        self.assertIn("DC Operating Point", body)

    def test_stylesheet_is_linked(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("style.css", body)

    def test_stylesheet_is_served(self):
        response = self.client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.content_type)
        self.assertIn(".badge", response.get_data(as_text=True))

    def test_region_badge_class_is_present(self):
        body = self.client.post("/", data=DEFAULTS).get_data(as_text=True)
        self.assertIn("badge-active", body)

    def test_raw_solution_note_is_shown(self):
        data = {**DEFAULTS, "r1": "100000", "r2": "1000"}
        body = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("raw solution", body)
        self.assertIn("nothing is clamped", body)

    def test_circuit_diagram_is_rendered(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertIn('role="img"', body)
        self.assertIn("circuit-title", body)
        for ref in ("VCC", "R1", "R2", "RC", "RE", "Q1"):
            self.assertIn(ref, body)

    def test_circuit_diagram_shows_default_values(self):
        body = self.client.get("/").get_data(as_text=True)
        for text in ("12 V", "47000 ohm", "10000 ohm", "4700 ohm", "1000 ohm"):
            self.assertIn(text, body)

    def test_circuit_diagram_reflects_submitted_value(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": "5"}).get_data(as_text=True)
        self.assertIn("5 V", body)
        self.assertNotIn("12 V", body)

    def test_circuit_diagram_shows_region_after_calculation(self):
        body = self.client.post("/", data=DEFAULTS).get_data(as_text=True)
        self.assertIn("circuit-region badge badge-active", body)

    def test_circuit_diagram_region_follows_cutoff(self):
        data = {**DEFAULTS, "r1": "100000", "r2": "1000"}
        body = self.client.post("/", data=data).get_data(as_text=True)
        self.assertIn("circuit-region badge badge-cutoff", body)

    def test_circuit_diagram_survives_validation_errors(self):
        body = self.client.post("/", data={**DEFAULTS, "vcc": "0"}).get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertIn("0 V", body)
        self.assertNotIn("circuit-region", body)

    def test_circuit_diagram_on_blank_form(self):
        body = self.client.post("/", data={}).get_data(as_text=True)
        self.assertIn('class="circuit"', body)
        self.assertNotIn("circuit-region", body)

    def test_circuit_diagram_handles_huge_values(self):
        response = self.client.post("/", data={**DEFAULTS, "vcc": "1000000"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("1000000 V", body)


DIVIDER = {**DEFAULTS, "r1": "100000", "r2": "22000", "rc": "2200",
           "amplitude_mv": "10", "frequency_hz": "1000"}
FIXED = {**DEFAULTS, "mode": "fixed"}


class TestSimulation(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def require_ngspice():
        try:
            resolve_ngspice()
        except SimulationError as exc:
            raise unittest.SkipTest(f"ngspice not available: {exc}") from exc

    def test_simulate_dc_shows_spice_and_analytical_labels(self):
        self.require_ngspice()
        r = self.client.post("/", data={**DIVIDER, "action": "simulate", "analysis": "dc"})
        body = r.get_data(as_text=True)
        self.assertIn("SPICE", body)
        self.assertIn("ngspice", body)
        self.assertIn("Analytical reference", body)
        self.assertIn(".model CEQ NPN", body)

    def test_simulate_rejects_zero_amplitude(self):
        r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                        "analysis": "tran", "amplitude_mv": "0"})
        body = r.get_data(as_text=True)
        self.assertIn("Amplitude", body)
        self.assertNotIn("Simulation complete", body)

    def test_simulate_rejects_zero_frequency(self):
        r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                        "analysis": "tran", "frequency_hz": "0"})
        body = r.get_data(as_text=True)
        self.assertIn("Frequency must be greater than 0.", body)
        self.assertNotIn("Simulation complete", body)

    def test_simulate_rejects_non_numeric_frequency(self):
        r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                        "analysis": "ac", "frequency_hz": "abc"})
        body = r.get_data(as_text=True)
        self.assertIn("Enter a finite number.", body)
        self.assertNotIn("Simulation complete", body)

    def test_simulate_rejects_tampered_analysis(self):
        r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                        "analysis": "bogus"})
        body = r.get_data(as_text=True)
        self.assertIn("Choose DC, AC, or Transient.", body)
        self.assertNotIn("Simulation complete", body)

    def test_bad_engine_path_shows_error_and_detail(self):
        with patch.dict(os.environ, {"NGSPICE_PATH": r"C:\nope\ngspice.exe"}):
            r = self.client.post("/", data={**DIVIDER, "action": "simulate",
                                            "analysis": "dc"})
        body = r.get_data(as_text=True)
        self.assertIn("Simulation error", body)
        self.assertIn(r"C:\nope", body)
        self.assertIn('class="engine-detail"', body)
        self.assertNotIn("data:image/png;base64,", body)

    def test_simulate_ac_renders_real_plot_data_uri(self):
        self.require_ngspice()
        r = self.client.post("/", data={**DIVIDER, "action": "simulate", "analysis": "ac"})
        body = r.get_data(as_text=True)
        self.assertIn("data:image/png;base64,", body)
        self.assertIn("Frequency (Hz)", body)
        self.assertIn("not determined in sweep range", body)

    def test_fixed_mode_ignores_simulate_action(self):
        r = self.client.post("/", data={**FIXED, "action": "simulate", "analysis": "ac"})
        body = r.get_data(as_text=True)
        self.assertIn("Fixed bias", body)
        self.assertNotIn("SPICE output", body)

    def test_emitter_mode_ignores_simulate_action(self):
        r = self.client.post("/", data={**DEFAULTS, "mode": "emitter",
                                        "action": "simulate", "analysis": "tran"})
        body = r.get_data(as_text=True)
        self.assertIn("Emitter bias", body)
        self.assertNotIn("SPICE output", body)


if __name__ == "__main__":
    unittest.main()
