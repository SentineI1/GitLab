import unittest

from app import app

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_shows_prefilled_form(self):
        response = self.client.get("/")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
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
        data = {
            **DEFAULTS, "vcc": "5", "r1": "10000", "r2": "10000",
            "rc": "1000", "re": "100", "beta": "300",
        }
        response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Saturation", body)
        self.assertIn("DC Operating Point", body)

    def test_invalid_post_shows_error_and_preserves_values(self):
        response = self.client.post("/", data={**DEFAULTS, "vcc": "0"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("DC Operating Point", body)
        self.assertIn("greater than 0", body)
        self.assertIn('value="47000"', body)

    def test_non_numeric_post_shows_error(self):
        response = self.client.post("/", data={**DEFAULTS, "r1": "abc"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("DC Operating Point", body)
        self.assertIn("Enter a finite number.", body)


if __name__ == "__main__":
    unittest.main()
