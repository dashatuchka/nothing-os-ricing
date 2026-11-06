"""Opt-in integration checks using the official Niri config and real Linux tools.

Run: NOTHING_ARCH_INTEGRATION=1 python3 -m unittest discover -s tests -v
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / 'scripts/install-nothing.py'


def stock_config():
    path = Path('/usr/share/doc/niri/default-config.kdl')
    if path.is_file():
        return path.read_bytes()
    # Arch's minimal Docker image may exclude /usr/share/doc on extraction.
    version = subprocess.check_output(['pacman', '-Q', 'niri'], text=True).split()[1]
    archives = sorted(Path('/var/cache/pacman/pkg').glob(f'niri-{version}-*.pkg.tar.zst'))
    if not archives:
        raise RuntimeError('Official Niri config is missing; install niri with its docs or retain its package cache')
    return subprocess.check_output(['bsdtar', '-xOf', str(archives[0]), 'usr/share/doc/niri/default-config.kdl'])


def file_snapshot(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


@unittest.skipUnless(os.environ.get('NOTHING_ARCH_INTEGRATION') == '1', 'requires an Arch test environment')
class CleanArchInstallation(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nothing-clean-profile-')
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.config = self.home / '.config'
        self.state = self.home / '.local/state'
        (self.config / 'niri').mkdir(parents=True)
        self.original = stock_config()
        (self.config / 'niri/config.kdl').write_bytes(self.original)
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), XDG_CONFIG_HOME=str(self.config), XDG_STATE_HOME=str(self.state),
                        PYTHONPYCACHEPREFIX=str(self.home / 'pycache'))

    def run_installer(self, *arguments, success=True):
        result = subprocess.run(['python3', str(INSTALLER), *map(str, arguments)],
                                env=self.env, cwd='/tmp', capture_output=True, text=True, timeout=60)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_stock_config_preview_install_rejection_and_exact_rollback(self):
        self.run_installer('--doctor')
        before = file_snapshot(self.config)
        preview = self.run_installer('--output', self.home / 'preview')
        self.assertIn('PREVIEW ONLY', preview.stdout)
        self.assertIn('Nothing has been installed', preview.stdout)
        self.assertIn('--apply', preview.stdout)
        self.assertEqual(file_snapshot(self.config), before)
        self.assertFalse((self.config / 'quickshell/nothing/launch.py').exists())

        installed = self.run_installer('--apply')
        self.assertIn('VERIFIED: installed launcher exists', installed.stdout)
        self.assertTrue((self.config / 'quickshell/nothing/launch.py').is_file())
        self.assertEqual(json.loads((self.config / 'nothing-niri/settings.json').read_text()), {'location': {}})
        subprocess.run(['niri', 'validate', '-c', str(self.config / 'niri/config.kdl')], check=True, env=self.env, capture_output=True)

        after = file_snapshot(self.config)
        self.run_installer('--apply', success=False)
        self.assertEqual(file_snapshot(self.config), after)
        backup = next((self.state / 'nothing-rice/full-shell-backups').iterdir())
        self.run_installer('--restore', backup)
        self.assertEqual(file_snapshot(self.config), before)
        self.assertEqual((self.config / 'niri/config.kdl').read_bytes(), self.original)

    def test_missing_config_and_conflicting_binding_leave_profile_untouched(self):
        niri = self.config / 'niri/config.kdl'
        niri.unlink()
        result = self.run_installer('--apply', success=False)
        self.assertIn('Niri config not found', result.stderr)
        self.assertFalse((self.config / 'quickshell').exists())
        text = self.original.decode().replace('binds {', 'binds {\n Mod+A { toggle-overview; }', 1)
        niri.write_text(text)
        before = file_snapshot(self.config)
        self.run_installer('--apply', success=False)
        self.assertEqual(file_snapshot(self.config), before)
        self.assertFalse((self.state / 'nothing-rice/full-shell-backups').exists())

    def test_preview_and_apply_cannot_be_combined(self):
        before = file_snapshot(self.config)
        result = self.run_installer('--apply', '--output', self.home / 'preview', success=False)
        self.assertIn('not allowed with argument', result.stderr)
        self.assertEqual(file_snapshot(self.config), before)


if __name__ == '__main__':
    unittest.main()
