pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Pipewire
import qs.services

Singleton {
    id: root
    property bool deckOpen: false
    property bool wallOpen: false
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property var mic: Pipewire.defaultAudioSource
    PwObjectTracker { objects: [root.sink, root.mic] }
    PwNodeLinkTracker { id: micUse; node: root.mic }
    readonly property bool live: micUse.linkGroups.length > 0
    readonly property real vol: sink?.audio?.volume ?? 0
    readonly property bool muted: sink?.audio?.muted ?? true
    readonly property real bri: Backlight.value
    readonly property bool hasBri: !!Backlight.dev
    readonly property string layout: Compositor.layout.slice(0, 2).toLowerCase()
    function setVol(value) {
        if (!sink?.audio) return;
        sink.audio.muted = false;
        sink.audio.volume = Math.max(0, Math.min(1, value));
    }
    function setBri(value) { Backlight.set(value); }
}
