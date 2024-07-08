import unittest

from . import defs, usb


class TestApi(unittest.TestCase):

    def test_log_parser(self):
        """Test parsing of receiver logs"""
        logs = """
Lock   (0x1f) Signal= -48.26dBm C/N= 10.60dB postBER= 0
          Layer A: Signal= 52.05% C/N= 53.05%
Lock   (0x1f) Signal= -48.19dBm C/N= 10.50dB postBER= 0
          Layer A: Signal= 52.05% C/N= 52.55%
"""
        expected_res = [{
            'lock': (True, None),
            'level': (-48.26, 'dBm'),
            'snr': (10.6, 'dB'),
            'ber': (0.0, None)
        }, {
            'lock': (True, None),
            'level': (-48.19, 'dBm'),
            'snr': (10.5, 'dB'),
            'ber': (0.0, None)
        }]

        res = []
        for line in logs.splitlines():
            parse_res = usb._parse_log(line)
            if (parse_res is not None):
                res.append(parse_res)

        self.assertListEqual(expected_res, res)

    def test_v4l_lnb_search(self):
        """Test searching of v4l-utils present LNBs"""

        for satellite, lnb, expected_v4l_lnb in [
            ("G18", ("GEOSATpro", "UL1PLL"), "UNIVERSAL"),
            ("T11N EU", ("Avenger", "PLL321S-2"), "UNIVERSAL"),
            ("T11N AFR", ("GEOSATpro", "UL1PLL"), "UNIVERSAL"),
            ("T18V Ku", ("Selfsat", "Integrated LNB"), "UNIVERSAL"),
            (
                "G18", ("Maverick", "MK1-PLL"), "QPH031"
            ),  # QPH031 because it can change the pol voltage and G18 is H-pol
            ("T11N EU", ("Maverick", "MK1-PLL"),
             "L10750"),  # L10750 can't change pol voltage but T11N EU is V-pol
            ("T18V C", ("Titanium", "C1-PLL"), "C-BAND")
        ]:
            info = {
                "sat": defs.get_satellite_def(satellite),
                "lnb": defs.get_lnb_def(*lnb)
            }
            v4l_lnb = usb._find_v4l_lnb(info)
            self.assertEqual(v4l_lnb['alias'], expected_v4l_lnb)
