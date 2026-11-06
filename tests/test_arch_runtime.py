"""Opt-in runtime smoke test: stock Niri config -> installer -> actual autostart.

Requires weston, Mesa/llvmpipe and dbus-run-session in addition to shell dependencies.
"""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

from test_arch_install import ROOT, stock_config


@unittest.skipUnless(os.environ.get('NOTHING_ARCH_RUNTIME') == '1', 'requires nested Wayland in Arch')
class FreshSessionRuntime(unittest.TestCase):
    def test_installed_shell_autostarts_and_opens_all_panels(self):
        with tempfile.TemporaryDirectory(prefix='nothing-runtime-') as directory:
            home = Path(directory)
            config = home / '.config'
            runtime = home / 'runtime'; runtime.mkdir(mode=0o700)
            (config / 'niri').mkdir(parents=True)
            (config / 'niri/config.kdl').write_bytes(stock_config())
            environment = os.environ.copy()
            environment.update(HOME=str(home), USER='smoketest', XDG_CONFIG_HOME=str(config),
                               XDG_STATE_HOME=str(home / '.local/state'), XDG_CACHE_HOME=str(home / '.cache'),
                               XDG_RUNTIME_DIR=str(runtime), WAYLAND_DISPLAY='outer',
                               LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', QT_QUICK_CONTROLS_STYLE='Basic')
            environment.pop('NIRI_SOCKET', None)
            installed = subprocess.run(['python3', str(ROOT / 'scripts/install-nothing.py'), '--apply'],
                                       env=environment, capture_output=True, text=True, timeout=60)
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            shell = config / 'quickshell/nothing'
            processes = []
            logs = []

            def start(command, name):
                handle = (home / name).open('w')
                logs.append(handle)
                process = subprocess.Popen(command, env=environment, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
                processes.append(process)
                return process

            def wait_for(check, seconds, description):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    result = check()
                    if result:
                        return result
                    if any(process.poll() is not None for process in processes):
                        break
                    time.sleep(0.2)
                details = '\n'.join(path.read_text() for path in home.glob('*.log'))
                self.fail(f'Timed out waiting for {description}\n{details}')

            try:
                start(['weston', '--backend=headless', '--renderer=pixman', '--width=1280', '--height=800',
                       '--socket=outer', '--idle-time=0', '--log=' + str(home / 'weston.log')], 'weston-stdout.log')
                wait_for(lambda: (runtime / 'outer').exists(), 15, 'headless Weston')
                # No command is passed after `--`: only the installed Niri autostart starts the shell.
                start(['dbus-run-session', '--', 'niri', '-c', str(config / 'niri/config.kdl')], 'niri.log')
                ipc_socket = wait_for(lambda: next(iter(runtime.glob('niri.*.sock')), None), 20, 'Niri socket')
                environment['NIRI_SOCKET'] = str(ipc_socket)
                environment['WAYLAND_DISPLAY'] = ipc_socket.name.rsplit('.', 2)[0][len('niri.'):]

                def ipc(method):
                    return subprocess.run(['qs', '-p', str(shell), 'ipc', 'call', 'nothing', method],
                                          env=environment, capture_output=True, text=True, timeout=5)

                wait_for(lambda: ipc('quick').returncode == 0, 30, 'installed shell autostart')
                self.assertEqual(ipc('quick').returncode, 0)
                for method in ['apps', 'calendar', 'dashboard', 'power']:
                    for _ in range(2):
                        result = ipc(method)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                log = subprocess.run(['qs', '-p', str(shell), 'log', '-t', '500', '--no-color'],
                                     env=environment, capture_output=True, text=True, timeout=10)
                self.assertEqual(log.returncode, 0, log.stderr)
                for error in ['Failed to load configuration', 'TypeError:', 'ReferenceError:', 'SyntaxError:', 'Binding loop']:
                    self.assertNotIn(error, log.stdout + log.stderr)
            finally:
                subprocess.run(['qs', '-p', str(shell), 'kill'], env=environment, capture_output=True, timeout=10)
                for process in reversed(processes):
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait(timeout=5)
                for handle in logs:
                    handle.close()


if __name__ == '__main__':
    unittest.main()
