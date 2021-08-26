import argparse
from unittest import TestCase
from unittest.mock import patch
from . import tsp


class TestTsp(TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        tsp.add_to_parser(self.parser)

    @patch('blocksatcli.util._ask_yes_or_no')
    def test_file_save_prompt(self, mock_yes_or_no):
        """Test tsp options that prompt the user for yes/no"""
        for opt in ['--ts-analysis', '--ts-file']:
            for resp in [False, True]:
                mock_yes_or_no.return_value = resp
                tsp_handler = tsp.Tsp()
                args = self.parser.parse_args([opt])
                self.assertEqual(tsp_handler.gen_cmd(args), resp)

    def test_non_prompting_opts(self):
        # If the prompting options are not provided, the tsp command should be
        # generated succesfully every time
        tsp_handler = tsp.Tsp()
        args = self.parser.parse_args(
            ['--ts-monitor-bitrate', '--ts-monitor-sequence'])
        self.assertTrue(tsp_handler.gen_cmd(args))

        # In this case, the output plugin should be "drop"
        self.assertEqual(tsp_handler.cmd[-1], 'drop')

    def test_print_to_stdout(self):
        args = self.parser.parse_args(['--ts-monitor-bitrate'])
        self.assertTrue(tsp.prints_to_stdout(args))

        args = self.parser.parse_args(['--ts-monitor-sequence'])
        self.assertTrue(tsp.prints_to_stdout(args))

        args = self.parser.parse_args(['--ts-dump'])
        self.assertTrue(tsp.prints_to_stdout(args))

        args = self.parser.parse_args(['--ts-file', '--ts-analysis'])
        self.assertFalse(tsp.prints_to_stdout(args))

        args = self.parser.parse_args([])
        self.assertFalse(tsp.prints_to_stdout(args))
