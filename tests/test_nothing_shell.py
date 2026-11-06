import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import os
import contextlib
import io

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


installer = module('installer', 'scripts/install-nothing.py')
events = module('events', 'config/quickshell/nothing/niri_events.py')


class NativeEvents(unittest.TestCase):
    def test_workspace_window_and_layout_lifecycle(self):
        state = events.State()
        state.event({'WorkspacesChanged': {'workspaces': [
            {'id': 10, 'idx': 1, 'output': 'eDP-1', 'is_focused': True, 'is_active': True},
            {'id': 20, 'idx': 2, 'output': 'eDP-1', 'is_focused': False, 'is_active': False},
            {'id': 30, 'idx': 1, 'output': 'DP-1', 'is_focused': False, 'is_active': True}
        ]}})
        state.event({'WindowsChanged': {'windows': [{'id': 5, 'workspace_id': 10, 'is_focused': True}]}})
        state.event({'WindowOpenedOrChanged': {'window': {'id': 6, 'workspace_id': 20, 'is_focused': True}}})
        self.assertFalse(state.windows[5]['is_focused'])
        state.event({'WorkspaceActivated': {'id': 20, 'focused': True}})
        snapshot = state.snapshot()
        self.assertEqual(snapshot['focused_workspace'], 20)
        self.assertTrue(next(w for w in snapshot['workspaces'] if w['id'] == 30)['is_active'])
        state.event({'KeyboardLayoutsChanged': {'keyboard_layouts': {'names': ['English (US)', 'Russian'], 'current_idx': 0}}})
        state.event({'KeyboardLayoutSwitched': {'idx': 1}})
        self.assertEqual(state.snapshot()['layout'], 'Russian')
        state.event({'WindowClosed': {'id': 6}})
        self.assertNotIn(6, state.windows)
        self.assertFalse(state.event({'WindowLayoutsChanged': {'changes': []}}))


class Installation(unittest.TestCase):
    def test_doctor_explains_missing_dependencies_without_writing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            (config / 'niri').mkdir()
            (config / 'niri/config.kdl').write_text('binds {\n Mod+D { spawn "fuzzel"; }\n}\n')
            before = set(config.rglob('*'))
            with mock.patch.object(installer.shutil, 'which', return_value=None), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertFalse(installer.diagnose(config))
            self.assertIn('MISSING: qs', output.getvalue())
            self.assertIn('sudo pacman -Syu --needed', output.getvalue())
            self.assertEqual(set(config.rglob('*')), before)

    def test_empty_xdg_variable_uses_default(self):
        with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': ''}):
            self.assertEqual(installer.xdg_path('XDG_CONFIG_HOME', '/tmp/normal-config'), Path('/tmp/normal-config').resolve())

    def test_missing_config_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'Start Niri once'):
                installer.read_config(Path(directory))

    def test_malformed_optional_weather_settings_do_not_block_install(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            (config / 'serpantinum').mkdir()
            (config / 'serpantinum/settings.json').write_text('broken JSON')
            with mock.patch.object(Path, 'home', return_value=config), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(installer.import_location(config), {})
            self.assertIn('configure the city after installation', output.getvalue())

    def test_location_import_excludes_unrelated_personal_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)
            (config / 'serpantinum').mkdir()
            (config / 'serpantinum/settings.json').write_text(json.dumps({'general': {'location': {
                'latitude': 52.52, 'longitude': 13.40, 'city': 'Berlin', 'ip': 'private-data', 'org': 'private-data'
            }}}))
            self.assertEqual(installer.import_location(config), {'latitude': 52.52, 'longitude': 13.40, 'city': 'Berlin'})

    def test_failed_apply_restores_all_previously_changed_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / 'source1', root / 'source2']
            targets = [root / 'target1', root / 'target2']
            for path in sources:
                path.write_text('new')
            for path in targets:
                path.write_text('original')
            original_copy = installer.copy_item

            def fail_second(source, target):
                if source == sources[1] and target == targets[1]:
                    raise OSError('simulated write failure')
                original_copy(source, target)

            with mock.patch.object(installer, 'copy_item', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'simulated'):
                    installer.apply(list(zip(sources, targets)), root / 'state')
            self.assertEqual([p.read_text() for p in targets], ['original', 'original'])

    def test_failed_restore_keeps_current_installation_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / 'backup'; backup.mkdir()
            targets = [root / 'target1', root / 'target2']
            manifest = []
            for index, target in enumerate(targets):
                target.write_text('current')
                (backup / str(index)).write_text('previous')
                manifest.append({'target': str(target), 'backup': str(index), 'existed': True})
            (backup / 'manifest.json').write_text(json.dumps(manifest))
            original_copy = installer.copy_item

            def fail_second(source, target):
                if source == backup / '1':
                    raise OSError('simulated restore failure')
                original_copy(source, target)

            with mock.patch.object(installer, 'copy_item', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'simulated'):
                    installer.restore(backup)
            self.assertEqual([p.read_text() for p in targets], ['current', 'current'])

    def test_niri_preserves_user_settings_and_removes_previous_shell_and_wallpaper(self):
        text = '''output "eDP-1" { scale 1.5; }
spawn-at-startup "serpantinumd" "start"
spawn-at-startup "swaybg" "-i" "/old/wall.jpg"
spawn-at-startup "waybar"
spawn-at-startup "mako"
spawn-at-startup "wl-paste" "--watch" "cliphist" "store"
binds {
 Mod+D { spawn "fuzzel"; }
 Mod+T { spawn "kitty"; }
 Mod+Down { focus-window-down; }
 Mod+Shift+Down { focus-monitor-down; }
 Mod+Space { toggle-overview; }
}
'''
        result = installer.adapt_niri(text, Path('/test/launch.py'))
        for old in ['"serpantinumd"', '"swaybg"', '"waybar"', '"mako"', '/old/wall.jpg']:
            self.assertNotIn(old, result)
        for keep in ['scale 1.5', '"wl-paste"', 'spawn "kitty"', 'toggle-overview', 'Mod+Down { focus-window-down; }']:
            self.assertIn(keep, result)
        self.assertIn('"ipc" "call" "nothing" "apps"', result)
        with self.assertRaises(ValueError):
            installer.adapt_niri(result, Path('/test/launch.py'))
        with self.assertRaises(ValueError):
            installer.adapt_niri(text.replace(' Mod+T', ' Mod+A'), Path('/test/launch.py'))

    def test_supplied_repository_niri_config_can_be_migrated(self):
        text = (ROOT / 'config/niri/config.kdl').read_text()
        result = installer.adapt_niri(text, Path('/test/launch.py'))
        self.assertIn('Mod+Shift+Down  { focus-monitor-down; }', result)

    def test_apply_and_restore_existing_and_new_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / 'stage'; stage.mkdir()
            (stage / 'shell').mkdir(); (stage / 'shell/test.qml').write_text('new shell')
            (stage / 'niri').write_text('new niri')
            config = root / 'config'; config.mkdir()
            (config / 'niri').write_text('original niri')
            state = root / 'state'
            installer.apply([(stage / 'shell', config / 'shell'), (stage / 'niri', config / 'niri')], state)
            backup = next((state / 'nothing-rice/full-shell-backups').iterdir())
            self.assertEqual((config / 'shell/test.qml').read_text(), 'new shell')
            installer.restore(backup)
            self.assertFalse((config / 'shell').exists())
            self.assertEqual((config / 'niri').read_text(), 'original niri')
            self.assertTrue(list(backup.glob('before-restore-*')))

    def test_all_shell_palette_literals_are_monochrome(self):
        import re
        for path in (ROOT / 'config/quickshell/nothing').rglob('*.qml'):
            for value in re.findall(r'#[0-9a-fA-F]{6}\b', path.read_text()):
                self.assertEqual(value[1:3].lower(), value[3:5].lower(), (path, value))
                self.assertEqual(value[3:5].lower(), value[5:7].lower(), (path, value))


if __name__ == '__main__':
    unittest.main()
