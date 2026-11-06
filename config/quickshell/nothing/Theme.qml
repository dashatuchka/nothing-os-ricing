pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    readonly property alias state: st
    readonly property bool light: st.light
    readonly property var greys: light
        ? ["#e9e9e9", "#ffffff", "#f1f1f1", "#d9d9d9", "#b8b8b8", "#6e6e6e", "#0b0b0b"]
        : ["#000000", "#0e0e0e", "#1a1a1a", "#2a2a2a", "#4a4a4a", "#8c8c8c", "#f2f2f2"]
    readonly property color bg: greys[0]
    readonly property color s1: greys[1]
    readonly property color s2: greys[2]
    readonly property color s3: greys[3]
    readonly property color mute: greys[4]
    readonly property color grey: greys[5]
    readonly property color fg: greys[6]
    readonly property color ink: bg
    readonly property color accent: fg
    readonly property color red: fg
    readonly property color glow: fade(fg, 0.6)
    readonly property color scrim: fade(bg, 0.84)
    // Ndot is never substituted under its name. Doto is the explicit bundled fallback.
    readonly property string dot: st.dotFamily || "Doto"
    readonly property string ui: "Space Grotesk"
    readonly property string mono: "Space Mono"
    readonly property string nf: "JetBrainsMono Nerd Font"
    FontLoader { source: Qt.resolvedUrl("fonts/Doto[ROND,wght].ttf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceGrotesk-Regular.otf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceGrotesk-Light.otf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceGrotesk-Medium.otf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceGrotesk-Bold.otf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceMono-Regular.ttf") }
    FontLoader { source: Qt.resolvedUrl("fonts/SpaceMono-Bold.ttf") }
    FontLoader { source: Quickshell.env("NOTHING_DOT_FONT_PATH") ? url(Quickshell.env("NOTHING_DOT_FONT_PATH")) : "" }
    readonly property real s: {
        const screen = Quickshell.screens[0];
        return screen ? Math.min(screen.width / 1920, screen.height / 1080) : 1;
    }
    readonly property var glide: [0.25, 1, 0.5, 1, 1, 1]
    readonly property int t: 350
    readonly property string riceState: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/nothing-niri"
    readonly property string wallCache: (Quickshell.env("XDG_CACHE_HOME") || Quickshell.env("HOME") + "/.cache") + "/nothing-niri/walls"
    function wallSrc(path) { return path ? `${wallCache}/${path.slice(path.lastIndexOf("/") + 1)}.jpg` : ""; }
    function url(path) { return path ? "file://" + path.split("/").map(encodeURIComponent).join("/") : ""; }
    function fade(color, alpha) { return Qt.rgba(color.r, color.g, color.b, alpha); }
    function hex(color) { return color.toString().slice(1, 7).toUpperCase(); }
    function corner(px) { return px * st.corners / 100; }
    function hh(date) { const h = date.getHours(); return st.clock24 ? String(h).padStart(2, "0") : String(h % 12 || 12); }
    function on(color) { return (color.r + color.g + color.b) / 3 > 0.5 ? "#000000" : "#ffffff"; }
    readonly property var styles: [{ head: "monochrome", items: [
        {name: "dark", pal: {c: ["#000000", "#0e0e0e"], accent: "#ffffff"}, fill: "#0e0e0e", now: !st.light, run: () => st.light = false},
        {name: "light", pal: {c: ["#e9e9e9", "#ffffff"], accent: "#000000"}, fill: "#ffffff", now: st.light, run: () => st.light = true}
    ]}]
    Component.onCompleted: stateFile.waitForJob()
    // Persistent home/bar state follows below; isolated from upstream Glyph state.
    FileView {
        id: stateFile
        path: root.riceState + "/glyph.json"
        blockLoading: true
        watchChanges: true
        onFileChanged: reload()
        // запись — раз в конце хода: writeAdapter() на каждое поле подряд путает соседние
        onAdapterUpdated: Qt.callLater(stateFile.writeAdapter)
        onLoadFailed: err => { if (err === FileViewError.FileNotFound) writeAdapter(); }

        JsonAdapter {
            id: st
            property string dotFamily: "Ndot 55"
            property bool light: false
            property string paint: ""     // откуда цвет: пусто — nothing, wall — обои, scheme — палитра
            property string scheme: "mocha" // какая палитра, id из schemes.js
            property int paintAt: 0       // какой из тонов обоев
            property var tones: []        // тона обоев, их пишет квантайзер; пусто — серые обои или нет картинки
            property string variant: "tonalspot" // как тон обоев становится палитрой, id из schemes.js (VARIANTS)
            property bool dnd: false  // новые не показываются, критические — всегда
            property int unread: 0    // для лока
            // ---- то, что крутят настройки (prefs) ----
            property var widgets: ["weather", "calendar", "battery", "player", "cava", "system"] // бенто дома по порядку, см. kinds
            property bool clock24: true
            property bool blink: true      // двоеточие часов мигает
            property string name: ""       // в приветствии; пусто — $USER
            property bool grid: true       // сетка точек на обоях
            property bool orb: true        // полутоновый шар
            // обои (пикер wall/Walls, рисует components/Wall): путь к картинке; пусто — сетка и шар. Папку пикера можно сменить здесь
            property string wall: ""
            property string wallDir: ""    // пусто — ~/Pictures/Wallpapers
            property int wallLook: 0       // 0 точки, 1 серое фото, 2 цвет
            property int wallPitch: 10     // шаг точек, px
            property int wallBright: 85    // %, от фона до картинки
            property string gif: ""        // гифка плитки-кота (services/Gifs), путь; пусто — первая в папке
            property string gifDir: ""     // пусто — ~/Pictures/Gifs
            property int rounding: 20      // окна hypr
            property int corners: 100      // углы панелей шелла, % от своих; круги остаются кругами (Theme.corner)
            property bool edges: true      // Glyph-полосы по краям (громкость/яркость, вспышки, прогресс)
            property int briSteps: 20      // яркость с клавиш: делений на шкалу, 40/20/10 — шаг 2.5/5/10 %
            property bool quickHover: true // быстрые настройки по наведению на правый край
            property bool deckHover: true  // deck — панель снизу по центру, вылезает по наведению на край
            property var deck: ["clock", "weather", "perf", "net", "media"] // её секции по порядку, см. decks
            property var bar: ["layout", "wifi", "bluetooth", "sound", "notes", "battery", "power"] // трей бара сверху вниз, см. bars
            property bool barTitle: true   // заголовок окна столбиком в баре
            property string barAt: "top" // left или top; за баром едут календарь, карточка батареи, дом, остров и вспышка Glyph
            // запись (quick/Rec, Sys.recArgs)
            property int recArea: 0        // 0 весь монитор, 1 область (slurp)
            property int recAudio: 0       // 0 без звука, 1 система, 2 микрофон, 3 оба одной дорожкой
            property int recFps: 60
            property int recQuality: 2     // medium, high, very_high, ultra
            property bool recCursor: true
        }
    }

    // виджеты бенто: id → ширина в ячейках (сетка 3 колонки × 3 ряда по 220). Не влезло — не показывается
    readonly property var kinds: ({ weather: 1, calendar: 1, cpu: 1, ram: 1, gpu: 1, disk: 1, battery: 1, buds: 1, player: 2, system: 3, cat: 1, cava: 1 })
    // секции deck
    readonly property var decks: ["clock", "weather", "perf", "net", "media"]
    // трей бара
    readonly property var bars: ["layout", "wifi", "bluetooth", "sound", "notes", "battery", "power", "cat"]

}
