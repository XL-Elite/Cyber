# CyberOS — demo Python desktop app

CyberOS is a small demo desktop application (PyQt6) — a safe GUI shell with:

- Dashboard: real-time CPU / memory / network stats (psutil)
- Integrated Terminal: run local shell commands and view output
- File browser: view files from your filesystem
- Tools tab: safe links and plugin hooks for user-provided extensions (no offensive tools included)
- Settings: light/dark theme and preferences

Important: this project contains *placeholders only* for security/penetration‑testing utilities. Do NOT use without proper authorization — see the legal/ethical note below.

## Quick start

1. Create a virtual environment and install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Run the app:

   python -m src.cyberos.main

## Build (PyInstaller)

A convenience script is provided: `./build.sh` — it runs PyInstaller and builds a single binary named `CyberOS`.

## Ethical / legal

Use this software only on systems you own or where you have explicit permission to test. The Tools tab only contains informational links and plugin hooks; it does not include active exploit code.

## Development

- Source: `src/cyberos`
- Main: `src/cyberos/main.py`
- UI: `src/cyberos/ui.py`

## License

MIT
