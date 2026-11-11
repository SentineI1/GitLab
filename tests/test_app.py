import unittest

from app import DEFAULTS, app


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


if __name__ == "__main__":
    unittest.main()
