import unittest
from unittest.mock import Mock

from backend.server import Handler


class DisconnectTests(unittest.TestCase):
    def test_cancelled_response_does_not_retry_as_server_error(self):
        for error in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            with self.subTest(error=error):
                handler = object.__new__(Handler)
                handler.send_response = Mock()
                handler.send_header = Mock()
                handler.end_headers = Mock()
                handler.wfile = Mock()
                handler.wfile.write.side_effect = error()
                handler.send(200, {'status': 'ok'})
                handler.send_response.assert_called_once_with(200)
                self.assertTrue(handler.close_connection)
