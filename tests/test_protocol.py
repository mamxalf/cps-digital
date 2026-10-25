import unittest

from rt400 import protocol


class TemperatureReport(unittest.TestCase):
    def test_example_from_vendor_binary_analysis(self):
        r = protocol.temperature_report(46.9)  # truncated to 46
        self.assertEqual(len(r), 64)
        self.assertEqual(r[:6].hex(), "07ffff000406")
        self.assertEqual(r[6:], bytes(58))

    def test_clamp(self):
        self.assertEqual(protocol.to_display_value(-5), 0)
        self.assertEqual(protocol.to_display_value(500), 199)

    def test_fahrenheit(self):
        self.assertEqual(protocol.to_display_value(50, "f"), 122)
        self.assertEqual(protocol.to_display_value(100, "f"), 199)  # 212 is clamped

    def test_digits(self):
        self.assertEqual(protocol.temperature_report(199)[3:6], bytes([1, 9, 9]))

    def test_version_report(self):
        r = protocol.version_report()
        self.assertEqual((r[0], r[1], len(r)), (7, 0xFD, 64))


if __name__ == "__main__":
    unittest.main()
