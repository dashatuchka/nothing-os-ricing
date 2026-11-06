#!/usr/bin/env python3
"""Translate Niri's native event stream to shell state, without polling."""
import json
import os
import socket
import sys


class State:
    def __init__(self):
        self.workspaces = []
        self.windows = {}
        self.layouts = {"names": [], "current_idx": 0}

    def event(self, message):
        if not isinstance(message, dict) or len(message) != 1:
            return False
        kind, data = next(iter(message.items()))
        if kind == "WorkspacesChanged":
            self.workspaces = data["workspaces"]
        elif kind == "WorkspaceActivated":
            active = next((w for w in self.workspaces if w["id"] == data["id"]), None)
            if active:
                for workspace in self.workspaces:
                    if workspace.get("output") == active.get("output"):
                        workspace["is_active"] = workspace["id"] == active["id"]
                    if data["focused"]:
                        workspace["is_focused"] = workspace["id"] == active["id"]
        elif kind == "WindowsChanged":
            self.windows = {w["id"]: w for w in data["windows"]}
        elif kind == "WindowOpenedOrChanged":
            window = data["window"]
            if window.get("is_focused"):
                for existing in self.windows.values():
                    existing["is_focused"] = False
            self.windows[window["id"]] = window
        elif kind == "WindowClosed":
            self.windows.pop(data["id"], None)
        elif kind == "WindowFocusChanged":
            for window in self.windows.values():
                window["is_focused"] = window["id"] == data["id"]
        elif kind == "KeyboardLayoutsChanged":
            self.layouts = data["keyboard_layouts"]
        elif kind == "KeyboardLayoutSwitched":
            self.layouts["current_idx"] = data["idx"]
        else:
            return False
        return True

    def snapshot(self):
        focused = next((w for w in self.workspaces if w.get("is_focused")), {})
        names = self.layouts["names"]
        index = self.layouts["current_idx"]
        return {"workspaces": sorted(self.workspaces, key=lambda w: (w.get("output") or "", w["idx"])),
                "windows": list(self.windows.values()), "focused_workspace": focused.get("id"),
                "output": focused.get("output", ""),
                "layout": names[index] if 0 <= index < len(names) else ""}


def main():
    path = os.environ.get("NIRI_SOCKET")
    if not path:
        sys.exit("NIRI_SOCKET is unset; start the shell inside the Niri session")
    state = State()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(path)
        connection.sendall(b'"EventStream"\n')
        with connection.makefile("r") as stream:
            reply = json.loads(stream.readline())
            if "Err" in reply:
                sys.exit(str(reply["Err"]))
            for line in stream:
                if state.event(json.loads(line)):
                    print(json.dumps(state.snapshot(), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
