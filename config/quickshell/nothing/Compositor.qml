pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    property var snapshot: ({workspaces: [], windows: [], layout: "", output: ""})
    readonly property var windows: snapshot.windows
    readonly property var workspaces: ({values: snapshot.workspaces.map(w => ({
        id: w.idx, uid: w.id, output: w.output, active: w.is_active,
        toplevels: {values: root.windows.filter(t => t.workspace_id === w.id)}
    }))})
    readonly property var focusedWorkspace: workspaces.values.find(w => w.uid === snapshot.focused_workspace) ?? null
    readonly property var focusedMonitor: ({name: snapshot.output, activeWorkspace: focusedWorkspace})
    function workspaceFor(output) { return workspaces.values.find(w => w.output === output && w.active) ?? null; }
    readonly property string layout: snapshot.layout
    readonly property var toplevels: ({values: windows.map(w => ({
        title: w.title, address: String(w.id), lastIpcObject: {class: w.app_id},
        workspace: {id: snapshot.workspaces.find(s => s.id === w.workspace_id)?.idx ?? 0}
    }))})
    function go(index) {
        if (String(index) === "-1") Quickshell.execDetached(["niri", "msg", "action", "focus-workspace-up"]);
        else if (String(index) === "+1") Quickshell.execDetached(["niri", "msg", "action", "focus-workspace-down"]);
        else Quickshell.execDetached(["niri", "msg", "action", "focus-workspace", String(index)]);
    }
    function focusWindow(id) { Quickshell.execDetached(["niri", "msg", "action", "focus-window", "--id", String(id)]); }
    function quit() { Quickshell.execDetached(["niri", "msg", "action", "quit"]); }
    Process {
        id: events
        running: true
        command: ["python3", Quickshell.shellPath("niri_events.py")]
        stdout: SplitParser {
            onRead: line => { try { root.snapshot = JSON.parse(line); } catch (error) { console.warn("Niri event:", error); } }
        }
        onExited: reconnect.restart()
    }
    Timer { id: reconnect; interval: 2000; onTriggered: events.running = true }
}
