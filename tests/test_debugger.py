import sys
import time
import socket
import unittest
import threading

import rr_mocks
g_host = rr_mocks.host()
g_game = rr_mocks.game(g_host)
g_realiylogger = rr_mocks.realitylogger(g_host)
sys.modules['host'] = g_host
sys.modules['game'] = g_game
sys.modules['game'].realitylogger = g_realiylogger

import rr_config
g_config = rr_config
sys.modules['rr_config'] = g_config

import rr_debugger


class TestDebugger(unittest.TestCase):

    def setUp(self):
        global g_host, g_realiylogger

        reload(rr_mocks)

        g_host = rr_mocks.host()
        g_game = rr_mocks.game(g_host)
        g_realiylogger = rr_mocks.realitylogger(g_game)
        sys.modules['host'] = g_host
        sys.modules['game'] = g_game
        sys.modules['game'].realitylogger = g_realiylogger

        reload(rr_debugger)

    def test_init_debugger(self):
        debugger = rr_debugger.Debugger()
        self.assertIsInstance(debugger, rr_debugger.Debugger)

    def test_filelogger_default_disabled(self):
        g_config.C['FILELOG'] = False
        debugger = rr_debugger.Debugger()

        self.assertTrue(rr_debugger.C['FILELOG'] is False)

    def test_filelogger_default_enabled(self):
        g_config.C['FILELOG'] = True
        debugger = rr_debugger.Debugger()

        self.assertTrue(rr_debugger.C['FILELOG'] is True)

    def test_filelogger_can_write_message_if_enabled(self):
        g_config.C['FILELOG'] = True
        test_message = 'debugger(filelogger(enabled))._debug_file'
        debugger = rr_debugger.Debugger()

        self.assertTrue(debugger._debug_file(test_message) is True)
        self.assertTrue(test_message in g_realiylogger.RealityLogger[
            debugger._logger_name].messages)

    def test_filelogger_cannot_write_message_if_disabled(self):
        g_config.C['FILELOG'] = False
        test_message = 'debugger(filelogger(disabled))._debug_file'
        debugger = rr_debugger.Debugger()

        self.assertTrue(debugger._debug_file(test_message) is False)
        with self.assertRaises(KeyError):
            g_realiylogger.RealityLogger[debugger._logger_name]

    # testing sockets
    def test_socket_client_default_disabled(self):
        g_config.C['SOCKET'] = False
        debugger = rr_debugger.Debugger()

        self.assertTrue(rr_debugger.C['SOCKET'] is False)
        self.assertTrue(debugger._client is None)

    def test_socket_client_default_enabled(self):
        g_config.C['SOCKET'] = True
        debugger = rr_debugger.Debugger()

        self.assertTrue(rr_debugger.C['SOCKET'] is True)
        self.assertIsInstance(debugger._client, socket.socket)

    def test_socket_client_can_send_message(self):
        g_config.C['SOCKET'] = True
        debugger = rr_debugger.Debugger()
        test_message = 'debugger(socket(enabled))._debug_socket'

        # Start fake server in background thread
        server = rr_mocks.MockNetwork(g_config).server
        server.exit_flags.append(test_message)
        server_thread = threading.Thread(target=server.runner_fake_server)
        server_thread.start()

        # Start client sending messages
        while 1:
            debugger._debug_socket(
                test_message, g_config.C['CLIENTHOST'], g_config.C['CLIENTPORT'])
            if test_message in server.messages:
                # Ensure server thread ends
                server_thread.join()
                break
            if not server_thread.isAlive():
                # skipping test if we could not create listening server
                self.skipTest('Failed to create UDP server thread')

        self.assertTrue(test_message in server.messages)
    
    def test_socket_client_should_not_send_message_if_disabled(self):
        g_config.C['SOCKET'] = False
        debugger = rr_debugger.Debugger()
        test_message = 'debugger(socket(disabled))._debug_socket'
        timeout_message = 'TIMEOUT'

        # Start fake server in background thread
        client = rr_mocks.MockNetwork(g_config).client
        server = rr_mocks.MockNetwork(g_config).server
        server.exit_flags.append(test_message)
        server.exit_flags.append(timeout_message)
        server_thread = threading.Thread(target=server.runner_fake_server)
        server_thread.start()
        
        start_time = time.time()
        timeout = 0.640 # seconds should be enough for everyone
        
        # Start client sending messages
        while 1:
            debugger._debug_socket(
                test_message, g_config.C['CLIENTHOST'], g_config.C['CLIENTPORT'])
            if test_message in server.messages:
                # Ensure server thread ends
                server_thread.join()
                break
            if not server_thread.isAlive():
                # skipping test if we could not create listening server
                self.skipTest('Failed to create UDP server thread')
            if time.time() - start_time > timeout:
                client.send_message(timeout_message, g_config.C['CLIENTHOST'], g_config.C['CLIENTPORT'])
                server_thread.join()
                break
        
        self.assertFalse(test_message in server.messages)

    def test_debugger_send_echo(self):
        test_message = 'debugger._debug_echo'
        debugger = rr_debugger.Debugger()

        debugger._debug_echo(test_message)
        self.assertTrue(test_message in g_host._game._state._echo)

    def test_debugger_send_ingame(self):
        test_message = 'debugger._debug_ingame'
        debugger = rr_debugger.Debugger()

        debugger._debug_ingame(test_message)
        self.assertTrue(test_message in g_host._game._state._chat["server"])
    
    def test_debugger_send_to_multiple_targets_ingame_echo(self):
        test_message = 'debugger.debugMessage(ingame, echo)'
        debugger = rr_debugger.Debugger()

        debugger.debugMessage(test_message, ['ingame', 'echo'])
        self.assertTrue(test_message in g_host._game._state._echo)
        self.assertTrue(test_message in g_host._game._state._chat["server"])
    
    def test_debugger_send_to_multiple_targets_default_echo(self):
        test_message = 'debugger.debugMessage()'
        debugger = rr_debugger.Debugger()

        debugger.debugMessage(test_message)
        self.assertTrue(test_message in g_host._game._state._echo)
    
    def test_debugger_send_to_multiple_targets_socket(self):
        g_config.C['SOCKET'] = True
        debugger = rr_debugger.Debugger()
        test_message = 'debugger.debugMessage(socket)'

        # Start fake server in background thread
        server = rr_mocks.MockNetwork(g_config).server
        server.exit_flags.append(test_message)
        server_thread = threading.Thread(target=server.runner_fake_server)
        server_thread.start()

        # Start client sending messages
        while 1:
            debugger.debugMessage(test_message, ['udp'])
            if test_message in server.messages:
                # Ensure server thread ends
                server_thread.join()
                break
            if not server_thread.isAlive():
                # skipping test if we could not create listening server
                self.skipTest('Failed to create UDP server thread')

        self.assertTrue(test_message in server.messages)
    
    def test_debugger_send_to_multiple_targets_filelogger(self):
        g_config.C['FILELOG'] = True
        test_message = 'debugger.debugMessage(file)'
        debugger = rr_debugger.Debugger()

        debugger.debugMessage(test_message, ['file'])
        self.assertTrue(test_message in g_realiylogger.RealityLogger[
            debugger._logger_name].messages)


if __name__ == '__main__':
    unittest.main()
