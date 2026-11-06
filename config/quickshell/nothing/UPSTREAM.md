# Glyph → Nothing for Niri

Visual components originate from Nebelung-cloud/glyph-rice:
https://github.com/Nebelung-cloud/glyph-rice

Snapshot: `2b4490b9bf4f3dc558b01e679ba150309cc799a3`.
License: GPL-3.0; see LICENSE-GPL-3.0. Bundled fonts retain fonts/OFL.txt.
Nothing/Glyph names are used descriptively; this is an unofficial fan customization.

Reused/adapted components: home, background, top bar, desktop widgets, launcher,
power menu, dashboard, Glyph notification/volume/brightness edges, shared visual
components and system/media/weather services. Original copyright remains with
the upstream authors. Local changes and new files in this directory are also
provided under GPL-3.0-or-later.

Local changes:

- Native Niri IPC state/event bridge replaces Hyprland imports and Lua dispatches.
- Top bar and strictly monochrome semantic color roles.
- Isolated Theme state and weather/font configuration; no upstream installer,
  compositor changes, greeter changes, or automatic app recoloring.
- Configurable real Ndot display font with regular weight; bundled Doto retained
  as an explicitly named alternative. Ndot itself is downloaded separately by
  request and is not redistributed in the repository.
- New calendar/orbital-weather panel based on the user's Serpentinum composition,
  using actual Open-Meteo hourly data; independent control center and launcher IPC.
- Existing swaylock remains responsible for locking the session.

The standalone installer and bridge tests are in the repository's scripts/ and
tests/ directories. Fonts, shaders and the original visual components are kept
with their corresponding sources.
