import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs
import qs.components
import qs.services

PanelWindow {
    id: root
    visible: false
    anchors { left: true; right: true; top: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "nothing-controls"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: Theme.fade(Theme.bg, 0.76)
    function toggle() { visible = !visible; }
    MouseArea { anchors.fill: parent; onClicked: root.visible = false }
    Item {
        anchors.fill: parent; focus: root.visible
        Keys.onEscapePressed: root.visible = false
        Stage {
            Rectangle {
                x: parent.width - width - 28; y: 105; width: 650; height: 900
                radius: 40; color: Theme.s1; border {width: 1; color: Theme.s3}
                MouseArea { anchors.fill: parent }
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 32; spacing: 24
                    RowLayout {
                        Layout.fillWidth: true
                        Num { text: "CONTROL"; font.pixelSize: 48; Layout.fillWidth: true }
                        Text {
                            text: "×"; color: Theme.grey; font.pixelSize: 30
                            MouseArea { anchors.fill: parent; anchors.margins: -8; onClicked: root.visible = false }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Action { label: "NETWORK"; onTapped: Quickshell.execDetached(["nm-connection-editor"]) }
                        Action { label: "BLUETOOTH"; onTapped: Quickshell.execDetached(["blueman-manager"]) }
                        Action { label: "AUDIO"; onTapped: Quickshell.execDetached(["pavucontrol"]) }
                    }
                    Lb { text: "VOLUME · " + Math.round(Sys.vol * 100) + "%" }
                    Level {
                        Layout.fillWidth: true; value: Sys.vol
                        onMoved: Sys.setVol(value)
                    }
                    Lb { visible: Sys.hasBri; text: "BRIGHTNESS · " + Math.round(Sys.bri * 100) + "%" }
                    Level {
                        visible: Sys.hasBri; Layout.fillWidth: true; value: Sys.bri
                        onMoved: Sys.setBri(value)
                    }
                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.s3 }
                    Lb { text: "HOME / WIDGETS" }
                    Flow {
                        Layout.fillWidth: true; Layout.preferredHeight: 100; spacing: 8
                        Repeater {
                            model: ["weather", "calendar", "battery", "player", "cava", "system"]
                            Rectangle {
                                required property string modelData
                                readonly property bool on: Theme.state.widgets.includes(modelData)
                                width: 172; height: 44; radius: 22
                                color: on ? Theme.fg : Theme.s2
                                Lb { anchors.centerIn: parent; text: modelData; color: parent.on ? Theme.ink : Theme.grey; px: 11 }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        const widgets = Theme.state.widgets.slice();
                                        const index = widgets.indexOf(modelData);
                                        if (index >= 0) widgets.splice(index, 1); else widgets.push(modelData);
                                        Theme.state.widgets = widgets;
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Action {
                            label: Theme.dot.toUpperCase()
                            onTapped: {
                                const ndot = Quickshell.env("NOTHING_NDOT_FAMILY");
                                if (ndot) Theme.state.dotFamily = Theme.dot === "Doto" ? ndot : "Doto";
                            }
                        }
                        Action { label: Theme.state.light ? "LIGHT" : "DARK"; onTapped: Theme.state.light = !Theme.state.light }
                        Action { label: Theme.state.dnd ? "DND ON" : "DND OFF"; onTapped: Theme.state.dnd = !Theme.state.dnd }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Lb { text: "NOTIFICATIONS"; Layout.fillWidth: true }
                        Lb {
                            text: "CLEAR"; color: Theme.fg
                            MouseArea { anchors.fill: parent; anchors.margins: -8; onClicked: Notes.clear() }
                        }
                    }
                    ListView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        clip: true; spacing: 10; model: Notes.list
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width; height: 98; radius: 20; color: Theme.s2
                            Column {
                                anchors.fill: parent; anchors.margins: 16; spacing: 6
                                Lb { width: parent.width; text: modelData.appName; elide: Text.ElideRight; px: 10 }
                                Text { width: parent.width; text: modelData.summary; color: Theme.fg; font {family: Theme.ui; pixelSize: 18} elide: Text.ElideRight }
                                Text { width: parent.width; text: modelData.body; textFormat: Text.PlainText; color: Theme.grey; font {family: Theme.ui; pixelSize: 13} elide: Text.ElideRight }
                            }
                            MouseArea { anchors.fill: parent; onClicked: modelData.dismiss() }
                        }
                        Lb { anchors.centerIn: parent; visible: Notes.list.length === 0; text: "ALL QUIET" }
                    }
                }
            }
        }
    }
    component Action: Rectangle {
        property string label
        signal tapped
        Layout.fillWidth: true; height: 54; radius: 27; color: Theme.s2
        Lb { anchors.centerIn: parent; text: parent.label; color: Theme.fg; px: 10 }
        MouseArea { anchors.fill: parent; onClicked: parent.tapped() }
    }
    component Level: Slider {
        id: level
        from: 0; to: 1; stepSize: 0.01
        background: Rectangle {
            x: level.leftPadding; y: (level.height - height) / 2
            width: level.availableWidth; height: 8; radius: 4; color: Theme.s3
            Rectangle { width: level.visualPosition * parent.width; height: parent.height; radius: 4; color: Theme.fg }
        }
        handle: Rectangle {
            x: level.leftPadding + level.visualPosition * (level.availableWidth - width)
            y: (level.height - height) / 2
            width: 22; height: 22; radius: 11; color: Theme.fg
        }
    }
}
