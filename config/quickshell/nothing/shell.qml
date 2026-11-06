import QtQuick
import Quickshell
import Quickshell.Io
import "home"
import "bar"
import "glyph"
import "launcher"
import "power"
import "deck"
import "panels"

ShellRoot {
    id: root
    Launcher { id: launcher }
    Glyph {}
    Power { id: powerPanel }
    Deck { id: deck }
    CalendarOrbit { id: calendarPanel }
    ControlCenter { id: control }
    Variants {
        model: Quickshell.screens
        Scope {
            required property var modelData
            Back { screen: modelData }
            Home { screen: modelData; onCalendarRequested: calendarPanel.toggle() }
            Bar {
                screen: modelData
                onMarkClicked: launcher.toggle()
                onTrayClicked: control.toggle()
                onClockClicked: calendarPanel.toggle()
                onPowerClicked: powerPanel.visible ? powerPanel.close() : powerPanel.open()
            }
        }
    }
    IpcHandler {
        target: "nothing"
        function apps() { launcher.toggle(); }
        function quick() { control.toggle(); }
        function calendar() { calendarPanel.toggle(); }
        function dashboard() { deck.toggle(); }
        function power() { powerPanel.visible ? powerPanel.close() : powerPanel.open(); }
    }
}
