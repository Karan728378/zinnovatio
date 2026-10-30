import unittest
from backend.app.db import load_config
from backend.app.logic import get_effective_mandate_share, validate_month_format

class TestMandateSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()

    def test_pre_mandate_dates(self):
        """Dates before 2025-11 must have a mandate share of 0.00."""
        self.assertEqual(get_effective_mandate_share("2024-10", self.cfg), 0.00)
        self.assertEqual(get_effective_mandate_share("2025-10", self.cfg), 0.00)

    def test_initial_mandate_2025_11(self):
        """2025-11 initiates the statutory 20% co-firing requirement."""
        self.assertEqual(get_effective_mandate_share("2025-11", self.cfg), 0.20)
        self.assertEqual(get_effective_mandate_share("2025-12", self.cfg), 0.20)
        self.assertEqual(get_effective_mandate_share("2026-05", self.cfg), 0.20)
        self.assertEqual(get_effective_mandate_share("2026-10", self.cfg), 0.20)

    def test_escalation_mandate_2026_11(self):
        """2026-11 escalates the co-firing requirement to 30%."""
        self.assertEqual(get_effective_mandate_share("2026-11", self.cfg), 0.30)
        self.assertEqual(get_effective_mandate_share("2027-01", self.cfg), 0.30)
        self.assertEqual(get_effective_mandate_share("2027-10", self.cfg), 0.30)

    def test_escalation_mandate_2027_11(self):
        """2027-11 escalates the co-firing requirement to 40%."""
        self.assertEqual(get_effective_mandate_share("2027-11", self.cfg), 0.40)
        self.assertEqual(get_effective_mandate_share("2028-05", self.cfg), 0.40)

    def test_escalation_mandate_2028_11(self):
        """2028-11 reaches the 50% statutory threshold."""
        self.assertEqual(get_effective_mandate_share("2028-11", self.cfg), 0.50)
        self.assertEqual(get_effective_mandate_share("2029-06", self.cfg), 0.50)

    def test_month_format_validation(self):
        """Rejects non-ISO YYYY-MM strings with ValueError."""
        self.assertTrue(validate_month_format("2026-11"))
        self.assertTrue(validate_month_format("2025-01"))

        invalid_inputs = ["2026-13", "2026-00", "2026", "2026/11", "Nov 2026", "2026-1", ""]
        for bad in invalid_inputs:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    validate_month_format(bad)
                with self.assertRaises(ValueError):
                    get_effective_mandate_share(bad, self.cfg)

if __name__ == "__main__":
    unittest.main()
