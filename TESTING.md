# Installation checks

The supported baseline is an existing Arch Linux + Niri session. Testing uses
the official Niri package's default config, not the personalized config in this
repository. All writes go to temporary user profiles.

## Python checks

```bash
python3 -m unittest discover -s tests -v
```

These run without third-party Python packages. Linux-only integration/runtime
checks are skipped unless explicitly enabled.

## Arch installation and rollback

With Niri, Quickshell, Python, fontconfig, curl and Swaylock installed:

```bash
NOTHING_ARCH_INTEGRATION=1 python3 -m unittest discover -s tests -v
```

The stock config is read from `/usr/share/doc/niri/default-config.kdl`. If the
minimal Arch image excluded documentation, the tests extract it from the official
Niri package in the pacman cache.

Covered scenarios:

- Empty profile, no Serpentinum settings and no Ndot download.
- Dependency/config diagnosis without changes.
- Preview leaves the live config unchanged and clearly states nothing was installed.
- Real `--apply`, an installed launcher and successful `niri validate`.
- Reapplication is rejected without modifying installed files.
- Rollback restores the original Niri config byte for byte and removes newly created files.
- Missing config and conflicting shortcuts stop before changing the profile.
- `--apply` and `--output` cannot be combined accidentally.
- Empty XDG variables use their standard fallback directories.
- Broken optional Serpentinum settings do not block installation.
- Weather migration excludes unrelated personal fields.
- Simulated write failures during apply and restore preserve the previous/current files.

## Actual session autostart

Add Weston, Mesa/llvmpipe and `dbus-run-session`:

```bash
NOTHING_ARCH_INTEGRATION=1 NOTHING_ARCH_RUNTIME=1 python3 -m unittest discover -s tests -v
```

The runtime test creates a fresh profile, installs the shell with the real CLI,
starts headless Weston and nested Niri, and relies entirely on the installed
Niri autostart to launch the shell. It does not launch Quickshell manually.

It waits for the shell's IPC endpoint, opens/closes apps, controls, calendar,
dashboard and power panels, then checks the log for QML/JavaScript load errors.
Test processes are stopped afterwards.

The suite was run both as root inside the test container and as an ordinary
unprivileged user. The full suite contains 16 tests.

## Continuous checks

[GitHub Actions](.github/workflows/checks.yml) runs Python checks and the Arch
installation/runtime suite on pushes and pull requests. The Arch job installs
current packages in an isolated container and runs tests as an ordinary user.
It does not use repository secrets or write to the host's desktop configuration.

## Limits

These checks verify a clean **user profile** on Arch, installation, autostart,
panel loading and rollback. They do not emulate a physical laptop, its greeter,
GPU driver, battery, Bluetooth adapter, microphone or brightness controller.
Existing systemd user services, custom Niri includes and unrelated shell
autostart entries can also differ from the default profile. Ndot downloading
and live weather depend on external services and are outside the repeatable
offline baseline. Passing CI is evidence for the tested scenario, not a promise
that every configuration will work unchanged.
