pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// CPU power profiles only. Display/input settings remain in the user's Niri config.
Singleton {
    id: root
    property var modes: []
    property int mode: 0
    readonly property int modeCount: modes.length
    readonly property int refreshHz: 60
    readonly property var rates: [60]
    Process {
        running: true
        command: ["sh", "-c", "command -v powerprofilesctl >/dev/null && powerprofilesctl list"]
        stdout: StdioCollector {
            onStreamFinished: {
                const found = [];
                let selected = 0;
                for (const line of text.split("\n")) {
                    const match = /^\s*(\*)?\s*(power-saver|balanced|performance):/.exec(line);
                    if (!match) continue;
                    if (match[1]) selected = found.length;
                    found.push({name: match[2], short: match[2].slice(0, 3), what: match[2]});
                }
                root.modes = found;
                root.mode = selected;
            }
        }
    }
    function setMode(index) {
        if (!modes[index]) return;
        profile.command = ["powerprofilesctl", "set", modes[index].name];
        profile.next = index;
        profile.running = true;
    }
    Process {
        id: profile
        property int next: 0
        onExited: code => { if (code === 0) root.mode = next; }
    }
}
