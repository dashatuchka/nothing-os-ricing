#!/usr/bin/env python3
"""Install the independent Glyph-based Nothing shell; preserve the previous session."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
FONT_URL = 'https://raw.githubusercontent.com/xeji01/nothingfont/main/fonts/Ndot57-Regular.otf'
FONT_SHA256 = '8f99a991d2cab1010eaf79520a7ba9bb17d287b4757ba99ae9ff99c4db44367c'
REQUIRED = {'niri': 'niri', 'qs': 'quickshell', 'fc-scan': 'fontconfig', 'curl': 'curl', 'swaylock': 'swaylock'}
OPTIONAL = {'cava': 'cava', 'brightnessctl': 'brightnessctl', 'pavucontrol': 'pavucontrol',
            'nm-connection-editor': 'network-manager-applet', 'blueman-manager': 'blueman',
            'powerprofilesctl': 'power-profiles-daemon'}


def xdg_path(variable, fallback):
    return Path(os.environ.get(variable) or fallback).expanduser().resolve()


def read_config(config):
    path = config / 'niri/config.kdl'
    if not path.is_file():
        raise ValueError(f'Niri config not found: {path}. Start Niri once to create it, or pass --config /your/config/directory.')
    return path.read_text()


def diagnose(config):
    print(f'Configuration directory: {config}')
    missing = []
    for program, package in REQUIRED.items():
        executable = shutil.which(program)
        print(f'{"OK" if executable else "MISSING"}: {program}' + (f' ({executable})' if executable else f' — package {package}'))
        if not executable:
            missing.append(package)
    for program, package in OPTIONAL.items():
        if not shutil.which(program):
            print(f'OPTIONAL: {program} is unavailable — package {package}')
    if missing:
        print('Install required packages: sudo pacman -Syu --needed ' + ' '.join(sorted(set(missing))))
    try:
        current = read_config(config)
        if 'NOTHING-NIRI-BEGIN' in current:
            print('Nothing is already configured. Use the documented rollback before reinstalling.')
        else:
            adapt_niri(current, config / 'quickshell/nothing/launch.py')
            print('OK: Niri configuration can be adapted')
    except (OSError, ValueError) as error:
        print(f'CONFIG ERROR: {error}')
        return False
    print('Diagnosis checks files and commands; device services are verified in your Niri session.')
    return not missing


def import_location(config):
    for path in [config / 'serpantinum/settings.json', Path.home() / 'serpantinum/settings.json']:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
            location = data.get('general', {}).get('location', {})
            if not isinstance(location, dict):
                raise ValueError('location is not an object')
            return {key: location[key] for key in ['latitude', 'longitude', 'city', 'timezone'] if key in location}
        except (OSError, ValueError, AttributeError, TypeError):
            print(f'NOTE: Could not import weather settings from {path}; configure the city after installation.')
    return {}


def adapt_niri(text, launcher):
    ipc = 'spawn "qs" "-p" ' + json.dumps(str(launcher.parent)) + ' "ipc" "call" "nothing" '
    # Only direct autostart entries are changed. Programs remain installed.
    text = re.sub(r'^\s*spawn-at-startup "(?:serpantinumd|waybar|mako|swaybg)"[^\n]*$', '', text, flags=re.M)
    text = re.sub(r'^\s*spawn-at-startup "(?:qs|quickshell)"[^\n]*$', '', text, flags=re.M)
    text = re.sub(r'^\s*spawn-sh-at-startup "[^\n]*(?:qs -c|quickshell -c)[^\n]*$', '', text, flags=re.M)
    if 'NOTHING-NIRI-BEGIN' in text:
        raise ValueError('Nothing shell is already configured; restore or update its own files instead')
    text, count = re.subn(r'^\s*Mod\+D(?=\s|\{)[^\n]*\{[^\n]*\}',
                         lambda _: '\n    Mod+D { ' + ipc + '"apps"; }', text, flags=re.M)
    if count != 1 or len(re.findall(r'^\s*binds\s*\{', text, re.M)) != 1:
        raise ValueError('Expected one Mod+D binding and one binds block; refusing an ambiguous edit')
    for key in ['Mod+A', 'Mod+N', 'Mod+Shift+D']:
        if re.search(r'^\s*' + re.escape(key) + r'(?=\s|\{)\s*(?:\{|[a-z])', text, re.M):
            raise ValueError(f'{key} is already used; refusing to overwrite it')
    bindings = '''
    // NOTHING-NIRI-BEGIN
    Mod+A { IPC "quick"; }
    Mod+N { IPC "calendar"; }
    Mod+Shift+D { IPC "dashboard"; }
    // NOTHING-NIRI-END
'''.replace('IPC', ipc)
    text = re.sub(r'(^\s*binds\s*\{)', lambda m: m[1] + bindings, text, count=1, flags=re.M)
    text += '\n// Independent Nothing shell; includes its own desktop background.\n'
    text += 'spawn-at-startup "python3" ' + json.dumps(str(launcher)) + '\n'
    return text


def copy_item(source, target):
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def restore(backup):
    manifest = json.loads((backup / 'manifest.json').read_text())
    for item in manifest:
        if item['existed'] and not (backup / item['backup']).exists():
            raise ValueError('Incomplete backup; nothing restored')
    saved = backup / ('before-restore-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    saved.mkdir()
    moved = []
    attempted = []
    try:
        for i, item in enumerate(manifest):
            target = Path(item['target'])
            if target.exists() or target.is_symlink():
                shutil.move(str(target), saved / str(i))
                moved.append((saved / str(i), target))
            attempted.append(target)
            if item['existed']:
                copy_item(backup / item['backup'], target)
    except BaseException:
        for target in reversed(attempted):
            if target.is_symlink():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        for current, target in reversed(moved):
            shutil.move(str(current), target)
        raise
    print(f'Restored previous session. Replaced files kept in {saved}')


def prepare(config, state, stage, dot_font=None, download_font=False):
    target_launcher = config / 'quickshell/nothing/launch.py'
    niri_text = adapt_niri(read_config(config), target_launcher)
    if dot_font and not dot_font.is_file():
        raise ValueError(f'Font file not found: {dot_font}. Use an existing --dot-font file, --download-ndot, or omit both to use bundled Doto.')
    shell = stage / 'shell'
    shutil.copytree(ROOT / 'config/quickshell/nothing', shell)
    settings = {'location': import_location(config)}
    family = 'Doto'
    if download_font:
        with urllib.request.urlopen(FONT_URL, timeout=30) as response:
            font_bytes = response.read(2_000_000)
        if hashlib.sha256(font_bytes).hexdigest() != FONT_SHA256:
            raise ValueError('Ndot download differs from inspected font; refusing installation')
        dot_font = stage / 'Ndot57-Regular.otf'
        dot_font.write_bytes(font_bytes)
    if dot_font:
        result = subprocess.run(['fc-scan', '--format', '%{family[0]}', str(dot_font)], check=True, capture_output=True, text=True)
        family = result.stdout.strip()
        if not family or 'ndot' not in family.lower():
            raise ValueError('The supplied file is not identified as an Ndot font by fontconfig')
        shutil.copy2(dot_font, shell / 'fonts/Ndot-display.otf')
        settings['dotFontPath'] = str(config / 'quickshell/nothing/fonts/Ndot-display.otf')
        settings['dotFontFamily'] = family
    (stage / 'settings.json').write_text(json.dumps(settings, indent=2, ensure_ascii=False) + '\n')
    (stage / 'glyph.json').write_text(json.dumps({
        'barAt': 'top', 'dotFamily': family, 'light': False, 'wall': '',
        'grid': True, 'orb': True,
        'widgets': ['weather', 'calendar', 'battery', 'player', 'cava', 'system'],
        'bar': ['layout', 'wifi', 'bluetooth', 'sound', 'notes', 'battery', 'power']
    }, indent=2) + '\n')
    (stage / 'config.kdl').write_text(niri_text)
    subprocess.run(['niri', 'validate', '-c', str(stage / 'config.kdl')], check=True)
    return [(shell, config / 'quickshell/nothing'),
            (stage / 'settings.json', config / 'nothing-niri/settings.json'),
            (stage / 'glyph.json', state / 'nothing-niri/glyph.json'),
            (stage / 'config.kdl', config / 'niri/config.kdl')], family


def apply(changes, state):
    backup = state / 'nothing-rice/full-shell-backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    manifest = []
    for index, (_, target) in enumerate(changes):
        # Refuse links: replacing a whole linked shell directory needs explicit handling.
        if target.is_symlink():
            raise ValueError(f'{target} is a symlink; no files changed')
        item = {'target': str(target), 'backup': str(index), 'existed': target.exists()}
        if target.exists():
            copy_item(target, backup / str(index))
        manifest.append(item)
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    # Keep replaced originals on the same filesystem until the transaction succeeds.
    held = []
    written = []
    try:
        for index, (source, target) in enumerate(changes):
            target.parent.mkdir(parents=True, exist_ok=True)
            old = target.with_name(target.name + '.nothing-previous-' + backup.name)
            if target.exists():
                target.rename(old)
                held.append((old, target))
            written.append(target)
            copy_item(source, target)
    except BaseException:
        for target in reversed(written):
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        for old, target in reversed(held):
            old.rename(target)
        raise
    for old, _ in held:
        if old.is_dir():
            shutil.rmtree(old)
        else:
            old.unlink()
    print(f'Installed independent Nothing shell. Backup: {backup}')
    print(f'Rollback: python3 {shlex.quote(str(Path(__file__).resolve()))} --restore {shlex.quote(str(backup))}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument('--doctor', action='store_true', help='Check dependencies and configuration without changing files')
    operation.add_argument('--apply', action='store_true', help='Apply from TTY after leaving Niri')
    operation.add_argument('--output', type=Path, help='Prepare files in a new directory without installing')
    parser.add_argument('--dot-font', type=Path, help='Use an existing Ndot .ttf/.otf')
    parser.add_argument('--download-ndot', action='store_true', help='Fetch inspected Ndot57 from the linked font mirror')
    operation.add_argument('--restore', type=Path)
    parser.add_argument('--config', type=Path, default=xdg_path('XDG_CONFIG_HOME', Path.home() / '.config'))
    parser.add_argument('--state', type=Path, default=xdg_path('XDG_STATE_HOME', Path.home() / '.local/state'))
    args = parser.parse_args()
    args.config = args.config.expanduser().resolve()
    args.state = args.state.expanduser().resolve()
    if args.dot_font:
        args.dot_font = args.dot_font.expanduser().resolve()
    try:
        if args.doctor:
            parser.exit(0 if diagnose(args.config) else 1)
        if args.restore:
            restore(args.restore)
            return
        if args.dot_font and args.download_ndot:
            parser.error('Use either --dot-font or --download-ndot')
        for program, package in REQUIRED.items():
            if not shutil.which(program):
                parser.error(f'Missing program: {program}. Install package {package}, then run --doctor.')
        if args.apply:
            with tempfile.TemporaryDirectory(prefix='nothing-install-') as directory:
                changes, family = prepare(args.config, args.state, Path(directory), args.dot_font, args.download_ndot)
                apply(changes, args.state)
        else:
            args.output = args.output.expanduser().resolve()
            args.output.mkdir(parents=True, exist_ok=False)
            changes, family = prepare(args.config, args.state, args.output, args.dot_font, args.download_ndot)
            print(f'PREVIEW ONLY: prepared in {args.output}. Nothing has been installed; no reboot is needed.')
            command = ['python3', str(Path(__file__).resolve()), '--apply', '--config', str(args.config), '--state', str(args.state)]
            if args.dot_font:
                command += ['--dot-font', str(args.dot_font.expanduser().resolve())]
            elif args.download_ndot:
                command.append('--download-ndot')
            print('After logging out of Niri, install from TTY: ' + shlex.join(command))
        print(f'Display font: {family}.')
        if args.apply:
            launcher = args.config / 'quickshell/nothing/launch.py'
            if not launcher.is_file():
                raise ValueError(f'Installation verification failed: {launcher} is missing. Use the printed rollback command.')
            print(f'VERIFIED: installed launcher exists at {launcher}')
            print('Installation complete. Keep the rollback command, reboot, and enter your Niri session.')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
