# square

A grey square that floats on top of everything on your Windows screen, so you can cover spoilers like the other-game scores on a sports broadcast.

## Install

Paste this into PowerShell on any Windows machine (no Python needed). Run it again to update.

```
irm https://raw.githubusercontent.com/wpinrui/square/main/install.ps1 | iex
```

It installs to `%LOCALAPPDATA%\square`, adds a Start menu shortcut, and launches Square. Square starts hidden with Windows unless you untick "Launch on startup" in the tray menu.

## Run from source

```
python -m pip install -r requirements.txt
python square.pyw
```

## Use

- **Unlocked** (white border): drag the middle to move, drag an edge or corner to resize.
- **Double-click** the square to lock it in place. Double-click again to unlock.
- **Tray icon** (by the clock): Show/Hide, Reset (100 by 100 square in the middle of the screen, unlocked), Launch on startup (ticked by default), Quit. Double-clicking the tray icon toggles Show/Hide.

Position, size and lock state are remembered between runs.

## Release

Push a `v*` tag (for example `git tag v0.2.0 && git push origin v0.2.0`). GitHub Actions builds `square.exe` and publishes it as a release, which the install script picks up.
