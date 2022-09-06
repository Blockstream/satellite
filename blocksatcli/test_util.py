import subprocess
from ipaddress import IPv4Address
from unittest import TestCase
from unittest.mock import patch

from . import util


class TestUserInputs(TestCase):

    @patch('builtins.input')
    def test_typed_input(self, mock_input):

        input_types = [str, int, float]
        user_inputs = ['string', 1, 1.0]
        mock_input.side_effect = user_inputs

        for i, input_type in enumerate(input_types):
            with self.subTest(input_type=input_type):
                res = util.typed_input('Input msg: ',
                                       in_type=input_type,
                                       default=None)
                self.assertEqual(res, user_inputs[i])

    @patch('builtins.input')
    def test_typed_input_type_error(self, mock_input):

        input_types = [int, float]
        valid_inputs = [1, 1.0]
        invalid_inputs = [
            1.0,  # float provided when int is expected
            'string'  # str provided when float is expected
        ]

        # Alternate invalid and valid inputs
        user_inputs = [None] * (len(valid_inputs) + len(invalid_inputs))
        user_inputs[::2] = invalid_inputs
        user_inputs[1::2] = valid_inputs
        mock_input.side_effect = user_inputs

        for i, input_type in enumerate(input_types):
            with self.subTest(input_type=input_type):
                res = util.typed_input('Input msg: ',
                                       in_type=input_type,
                                       default=None)
                self.assertEqual(res, valid_inputs[i])

    @patch('builtins.input')
    def test_typed_input_ipv4addr(self, mock_input):
        input_types = [IPv4Address]
        user_inputs = [
            '192.168.0',  # invalid input
            '192.168.0.1'  # valid input
        ]
        expected = IPv4Address('192.168.0.1')
        mock_input.side_effect = user_inputs

        for i, input_type in enumerate(input_types):
            with self.subTest(input_type=input_type):
                res = util.typed_input('Input msg: ',
                                       in_type=input_type,
                                       default=None)
                self.assertEqual(res, expected)


class TestRunner(TestCase):

    @patch('subprocess.run')
    def test_process_runner_run_cmd(self, mock_subprocess):
        # Run process runner with sudo
        runner = util.ProcessRunner()
        runner.run(cmd=['echo', 'test'], root=True)
        mock_subprocess.assert_called_with(['sudo', 'echo', 'test'],
                                           cwd=None,
                                           env=None,
                                           stdout=None,
                                           stderr=None,
                                           check=True)

        # Run process runner with sudo and capture the output
        runner = util.ProcessRunner()
        runner.run(cmd=['echo', 'test'], root=True, capture_output=True)
        mock_subprocess.assert_called_with(['sudo', 'echo', 'test'],
                                           cwd=None,
                                           env=None,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           check=True)
