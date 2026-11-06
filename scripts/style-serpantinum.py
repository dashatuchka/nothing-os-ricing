#!/usr/bin/env python3
"""Patch the user's inspected Serpentinum revision; preview by default."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil

HERE = Path(__file__).resolve().parent
EXPECTED = {
    "calendar/CalendarPopup.qml": "8c8788be36abd5e18cbeaae643cec560ce193776250d350a1dfa98ceb24b08f8",
    "singletons/theme/ThemeBackend.qml": "bfe2c41219ca4356b7a2b9a73bc65ca4e46c05def720b8bce34f7a5fd10aa024",
}


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected source near {old[:70]!r}; no files changed")
    return text.replace(old, new, 1)


def calendar(text):
    text = once(text, "return Scaler.s(val);", "return Scaler.s(val) * 0.84;")
    # Keep the original three-column composition; fit the laptop's logical width.
    text = re.sub(r"    property color activeWeatherHex: \{.*?\n    \}",
                  "    property color activeWeatherHex: window.text", text, count=1, flags=re.S)
    text = once(text, '(modelData ? (modelData.hex || window.text) : window.text)', 'window.text')
    text = once(text, 'font.family: ThemeBackend.fontFamily\n                    font.pixelSize: window.s(520)',
                'font.family: ThemeBackend.iconFont\n                    font.pixelSize: window.s(520)')
    text = once(text, 'font.family: ThemeBackend.fontFamily\n                                        font.pixelSize: window.s(16.5)',
                'font.family: ThemeBackend.iconFont\n                                        font.pixelSize: window.s(16.5)')
    for anchor in ['text: DateTime.time', 'text: (window.weatherData && window.weatherData.offline ? "--" : window.displayedTemp.toFixed(1)) + (Weather.unitSym || "°")']:
        text = once(text, anchor + '\n' + (' ' * (24 if anchor == 'text: DateTime.time' else 28)) + 'font.family: ThemeBackend.fontFamily',
                    anchor + '\n' + (' ' * (24 if anchor == 'text: DateTime.time' else 28)) + 'font.family: ThemeBackend.dotFontFamily')
    text = text.replace('font.family: ThemeBackend.dotFontFamily\n                        font.weight: Font.Black',
                        'font.family: ThemeBackend.dotFontFamily\n                        font.weight: Font.Normal')
    text = text.replace('font.family: ThemeBackend.dotFontFamily\n                            font.weight: Font.Black',
                        'font.family: ThemeBackend.dotFontFamily\n                            font.weight: Font.Normal')
    text = once(text, 'scale: 0.98 + (0.02 * window.secondPulse)', 'scale: 1.0')
    # A steady central clock, retaining entrance and forecast transition animations.
    start = text.index('                transform: [', text.index('id: centralHub'))
    end = text.index('\n                ShaderEffect {', start)
    text = text[:start] + '                transform: Translate { y: window.s(25) * (1.0 - introClock) }\n' + text[end:]
    text = once(text, 'border.width: 0\n            border.color: "transparent"',
                'border.width: 1\n            border.color: window.surface1')
    text = once(text, 'color: calendarGlass.active ? "transparent" : Qt.alpha(window.surface0, 0.2)',
                'color: calendarGlass.active ? "transparent" : window.surface0')
    text = once(text, 'border.color: Qt.alpha(window.surface1, 0.4)', 'border.color: window.surface1')
    text = once(text, 'cornerRadius: window.s(5)', 'cornerRadius: window.s(18)')
    text = once(text, 'color: window.overlay0\n                                horizontalAlignment:',
                'color: window.subtext0\n                                horizontalAlignment:')
    marker = '                id: weatherContainer\n'
    text = once(text, marker, marker + '''
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -window.s(14)
                    radius: ThemeBackend.borderRadius
                    color: window.surface0
                    border.width: 1
                    border.color: window.surface1
                    z: -1
                }
''')
    # Dot-grid clock face behind the existing hourly weather orbit.
    marker = '                ShaderEffect {\n                    id: orbitCanvas'
    text = once(text, marker, '''                Rectangle {
                    anchors.centerIn: parent
                    width: window.s(330)
                    height: width
                    radius: width / 2
                    color: window.mantle
                    border.width: 1
                    border.color: window.surface1
                    z: -20
                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);
                            ctx.fillStyle = "#303030";
                            const step = window.s(14);
                            for (let x = step; x < width; x += step) {
                                for (let y = step; y < height; y += step) {
                                    if (Math.hypot(x - width / 2, y - height / 2) < width / 2 - step) {
                                        ctx.beginPath();
                                        ctx.arc(x, y, window.s(0.8), 0, Math.PI * 2);
                                        ctx.fill();
                                    }
                                }
                            }
                        }
                    }
                }

''' + marker)
    return text


def theme(text):
    text = once(text, '    property int borderRadius: 8', '''    // Nothing adaptation: readable interface, separate display numerals.
    property string dotFontFamily: "Ndot 55"
    FontLoader {
        source: {
            const path = root.availableFontPaths[root.dotFontFamily.toLowerCase()];
            return path ? "file://" + path : "";
        }
    }
    property int borderRadius: 8''')
    return once(text, '        if (themeConfig.borderRadius !== undefined) {', '''        root.dotFontFamily = themeConfig.dotFontFamily || "Ndot 55";
        if (themeConfig.borderRadius !== undefined) {''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / '.local/share/serpantinum/src/quickshell')
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    parser.add_argument('--config', type=Path, default=config)
    parser.add_argument('--dot-font', default='Ndot 55', help='Installed font family for large numerals')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path, help='Preview directory; must not exist')
    parser.add_argument('--restore', type=Path, help='Restore from a backup made by this script')
    args = parser.parse_args()
    if args.restore:
        manifest = json.loads((args.restore / 'manifest.json').read_text())
        # Preserve the current state as well, so rollback itself is reversible.
        saved = args.restore / ('before-restore-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        saved.mkdir()
        for i, item in enumerate(manifest):
            target = Path(item['target'])
            if target.exists():
                shutil.copy2(target, saved / str(i))
            shutil.copy2(args.restore / str(i), target)
        print(f'Restored. Previous contents saved in {saved}. Restart the session.')
        return
    changes = {}
    required = [args.source / relative for relative in EXPECTED]
    required += [args.config / 'serpantinum/settings.json', args.config / 'niri/config.kdl']
    for path in required:
        if not path.is_file():
            parser.error(f'Missing file: {path}. Check --source and --config; live files unchanged.')
    for relative, expected in EXPECTED.items():
        path = args.source / relative
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            parser.error(f'{path} differs from inspected version; refusing to patch')
        changes[path] = (calendar if relative.startswith('calendar/') else theme)(data.decode())
    settings_path = args.config / 'serpantinum/settings.json'
    current = json.loads(settings_path.read_text())
    merge = runpy.run_path(str(HERE / 'prepare-serpantinum.py'))['merge']
    preset = json.loads((HERE.parent / 'presets/serpantinum/nothing-monochrome.json').read_text())
    preset['theme']['dotFontFamily'] = args.dot_font
    changes[settings_path] = json.dumps(merge(current, preset), indent=2, ensure_ascii=False) + '\n'
    niri_path = args.config / 'niri/config.kdl'
    niri = niri_path.read_text()
    niri = re.sub(r'^\s*spawn-at-startup "(?:waybar|mako)"[^\n]*$', '', niri, flags=re.M)
    if not re.search(r'^\s*spawn-at-startup "serpantinumd" "start"', niri, flags=re.M):
        niri += '\nspawn-at-startup "serpantinumd" "start"\n'
    changes[niri_path] = niri
    if not args.apply:
        if not args.output:
            parser.error('Choose --output DIRECTORY for preview or --apply from TTY')
        args.output.mkdir(parents=True, exist_ok=False)
        for i, (target, content) in enumerate(changes.items()):
            (args.output / f'{i}-{target.name}').write_text(content)
        print(f'Preview: {args.output}; live files unchanged')
        return
    backup = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'nothing-rice/serpantinum-backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    manifest = []
    # Back up every file before the first write. Restore on a write failure.
    for i, target in enumerate(changes):
        shutil.copy2(target, backup / str(i))
        manifest.append({'target': str(target.resolve())})
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    try:
        for target, content in changes.items():
            target.write_text(content)
    except BaseException:
        for i, target in enumerate(changes):
            shutil.copy2(backup / str(i), target)
        raise
    print(f'Applied. Backup: {backup}')
    print(f'Rollback: python3 scripts/style-serpantinum.py --restore {backup}')
    print('Validate with niri validate before entering the session.')


if __name__ == '__main__':
    main()
