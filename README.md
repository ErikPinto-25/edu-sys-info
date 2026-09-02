# edu-sys-info

Educational desktop application that displays a small, documented set of system and
network information and can optionally send those exact values to a Discord webhook.

## What it collects

- Hostname
- Local IPv4 address
- Public IP address (queried from `https://api.ipify.org`)

The application displays the information locally before anything can be sent. Remote
sharing requires a valid Discord webhook, an explicit consent checkbox and a final
confirmation dialog.

## Run from source on Windows

Requirements:

- Windows 10 or Windows 11
- Python 3.10 or newer, including Tkinter

In PowerShell, from the project folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Build the Windows executable

Double-click `build.bat`. It creates an isolated virtual environment, installs the
build dependencies and generates:

```text
dist\EduSysInfo.exe
```

The resulting executable includes the Python runtime, so the destination computer
does not need Python installed. Python is required only on the computer performing
the build.

The equivalent manual command is:

```powershell
python -m pip install -r requirements-dev.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed --name EduSysInfo main.py
```

PyInstaller does not cross-compile: build the Windows `.exe` on Windows. The included
GitHub Actions workflow also builds it on a Windows runner and uploads an artifact
named `EduSysInfo-Windows`.

## Configure Discord sharing

Paste a Discord webhook URL into the masked field in the application. The value is
used only for the current process and is not saved by the project.

Optionally, define it before launching the app:

```powershell
$env:EDU_SYS_INFO_WEBHOOK_URL = "https://discord.com/api/webhooks/.../..."
python main.py
```

Never commit a real webhook URL. A leaked webhook should be deleted or regenerated
from Discord immediately.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Ethical notice

Use this project only on computers you own or are explicitly authorized to inspect.
Do not remove the consent flow, conceal execution or collect additional information
without clearly disclosing it to the user.

## Project structure

```text
edu-sys-info/
├── .github/workflows/build-windows.yml
├── tests/test_main.py
├── .gitignore
├── build.bat
├── main.py
├── requirements-dev.txt
└── requirements.txt
```

## License

This project is distributed under the MIT License. See `LICENSE`.
