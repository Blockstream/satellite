import unittest
from . import usb


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
