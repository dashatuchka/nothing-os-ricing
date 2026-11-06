import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs
import qs.components
import qs.services

// Serpentinum's calendar / orbital forecast / current-weather composition,
// rebuilt using the Glyph visual system and independent of Serpentinum services.
PanelWindow {
    id: root
    visible: false
    anchors { left: true; right: true; top: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "nothing-calendar"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: visible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: Theme.fade(Theme.bg, 0.76)
    function toggle() { visible = !visible; if (visible) { monthOffset = 0; Weather.refresh(); } }
    property int monthOffset: 0
    property int selectedHour: 0
    SystemClock { id: clock; precision: SystemClock.Seconds }
    readonly property var month: new Date(clock.date.getFullYear(), clock.date.getMonth() + monthOffset, 1)
    readonly property int startDay: (month.getDay() + 6) % 7
    readonly property int monthLength: new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate()
    MouseArea { anchors.fill: parent; onClicked: root.visible = false }
    Item {
        anchors.fill: parent
        focus: root.visible
        Keys.onEscapePressed: root.visible = false
        Keys.onLeftPressed: root.monthOffset--
        Keys.onRightPressed: root.monthOffset++
        Stage {
            Rectangle {
                id: panel
                anchors.centerIn: parent
                width: 1740
                height: 640
                radius: 44
                color: Theme.s1
                border { width: 1; color: Theme.s3 }
                MouseArea { anchors.fill: parent }
                Lb { x: 32; y: 24; text: "( NOTHING / DAY VIEW )"; px: 11 }
                Text {
                    x: parent.width - 60; y: 18; text: "×"
                    color: Theme.grey; font {family: Theme.ui; pixelSize: 30}
                    MouseArea { anchors.fill: parent; anchors.margins: -10; onClicked: root.visible = false }
                }
                Rectangle {
                    x: 28; y: 70; width: 390; height: 540
                    radius: 34; color: Theme.s2
                    RowLayout {
                        x: 22; y: 24; width: parent.width - 44
                        Text {
                            text: "‹"; color: Theme.fg; font.pixelSize: 28
                            MouseArea { anchors.fill: parent; anchors.margins: -8; onClicked: root.monthOffset-- }
                        }
                        Lb {
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignHCenter
                            text: Qt.formatDate(root.month, "MMMM yyyy"); color: Theme.fg
                        }
                        Text {
                            text: "›"; color: Theme.fg; font.pixelSize: 28
                            MouseArea { anchors.fill: parent; anchors.margins: -8; onClicked: root.monthOffset++ }
                        }
                    }
                    GridLayout {
                        x: 16; y: 94; width: parent.width - 32; height: 380
                        columns: 7; columnSpacing: 3; rowSpacing: 6
                        Repeater {
                            model: ["M", "T", "W", "T", "F", "S", "S"]
                            Lb {
                                required property string modelData
                                Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter
                                text: modelData; px: 11
                            }
                        }
                        Repeater {
                            model: 42
                            Rectangle {
                                required property int index
                                readonly property int day: index - root.startDay + 1
                                readonly property bool valid: day >= 1 && day <= root.monthLength
                                readonly property bool today: valid && root.monthOffset === 0 && day === clock.date.getDate()
                                Layout.fillWidth: true; Layout.fillHeight: true
                                radius: width / 2
                                color: today ? Theme.fg : "transparent"
                                Text {
                                    anchors.centerIn: parent; text: parent.valid ? parent.day : ""
                                    font { family: Theme.mono; pixelSize: 15 }
                                    color: parent.today ? Theme.ink : Theme.fg
                                }
                            }
                        }
                    }
                    Lb {
                        anchors { bottom: parent.bottom; bottomMargin: 24; horizontalCenter: parent.horizontalCenter }
                        text: root.monthOffset ? "BACK TO TODAY" : Qt.formatDate(clock.date, "dddd")
                        MouseArea { anchors.fill: parent; anchors.margins: -12; onClicked: root.monthOffset = 0 }
                    }
                }
                Item {
                    x: 440; y: 70; width: 820; height: 540
                    Rectangle {
                        anchors.centerIn: parent; width: 340; height: width; radius: width / 2
                        color: Theme.bg; border {width: 1; color: Theme.s3}
                        Ring { anchors.fill: parent; anchors.margins: 16; n: 60; dot: 2; f: clock.date.getSeconds() / 60 }
                        Column {
                            anchors.centerIn: parent; spacing: 18
                            Num { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatTime(clock.date, "HH:mm"); font.pixelSize: 78 }
                            Lb { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatDate(clock.date, "ddd · d MMM"); px: 12 }
                        }
                    }
                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            const ctx = getContext("2d"); ctx.clearRect(0, 0, width, height);
                            ctx.fillStyle = "#444444";
                            for (let i = 0; i < 72; i++) {
                                const a = i * Math.PI * 2 / 72;
                                ctx.beginPath(); ctx.arc(width / 2 + Math.cos(a) * 340, height / 2 + Math.sin(a) * 218, 1.5, 0, Math.PI * 2); ctx.fill();
                            }
                        }
                    }
                    Repeater {
                        model: Weather.hours
                        Rectangle {
                            required property var modelData
                            required property int index
                            readonly property real angle: index * Math.PI * 2 / Math.max(1, Weather.hours.length) - Math.PI / 2
                            readonly property bool selected: index === root.selectedHour
                            x: 410 + Math.cos(angle) * 340 - width / 2
                            y: 270 + Math.sin(angle) * 218 - height / 2
                            width: 64; height: 92; radius: 32
                            color: selected ? Theme.fg : Theme.s2
                            border {width: 1; color: Theme.s3}
                            Column {
                                anchors.centerIn: parent; spacing: 7
                                Lb { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatTime(modelData.date, "HH:mm"); px: 10; color: selected ? Theme.ink : Theme.grey }
                                Icon { anchors.horizontalCenter: parent.horizontalCenter; text: Weather.glyph(modelData.code, modelData.day); font.pixelSize: 22; color: selected ? Theme.ink : Theme.fg }
                                Lb { anchors.horizontalCenter: parent.horizontalCenter; text: Math.round(modelData.temp) + "°"; color: selected ? Theme.ink : Theme.fg; px: 12 }
                            }
                            MouseArea { anchors.fill: parent; onClicked: root.selectedHour = index }
                        }
                    }
                    Lb {
                        visible: Weather.hours.length === 0
                        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter }
                        text: "WAITING FOR HOURLY FORECAST"; px: 10
                    }
                }
                Rectangle {
                    x: 1280; y: 70; width: 432; height: 540; radius: 34; color: Theme.s2
                    Column {
                        x: 30; y: 28; width: parent.width - 60; spacing: 18
                        Lb { text: "CURRENT WEATHER" }
                        Icon { text: Weather.glyph(Weather.now?.code ?? 3, Weather.now?.day); font.pixelSize: 70 }
                        Num { text: Weather.ok ? Math.round(Weather.now.temp) + "°" : "--"; font.pixelSize: 110 }
                        Text { width: parent.width; text: Quickshell.env("NOTHING_CITY") || ""; color: Theme.fg; font {family: Theme.ui; pixelSize: 26} elide: Text.ElideRight }
                        Lb { text: Weather.ok ? Weather.name(Weather.now.code) : "CONNECTING" }
                        Rectangle { width: parent.width; height: 1; color: Theme.s3 }
                        Grid {
                            columns: 2; rowSpacing: 20; columnSpacing: 32
                            Repeater {
                                model: [
                                    ["WIND", Weather.ok ? Weather.now.wind + " m/s" : "--"],
                                    ["HUMIDITY", Weather.ok ? Weather.now.humidity + "%" : "--"],
                                    ["RAIN", Weather.ok ? (Weather.now.rain ?? "--") + "%" : "--"],
                                    ["FEELS", Weather.ok ? Math.round(Weather.now.feels) + "°" : "--"]
                                ]
                                Column {
                                    required property var modelData
                                    width: 150; spacing: 6
                                    Lb { text: modelData[0]; px: 10 }
                                    Text { text: modelData[1]; color: Theme.fg; font {family: Theme.mono; pixelSize: 18} }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
