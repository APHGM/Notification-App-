# Application Running Notifier

A cross-platform desktop application built with **PyQt6** to monitor and notify when selected GUI applications are running.  
It runs silently in the **system tray** and sends notifications whenever monitored applications are detected.  

---

## ✨ Features

- 🔍 **Monitor user-selected applications** (via file selection or double-clicking from running apps).
- 🖥️ **GUI-Only Filtering** – Ignores background/system processes for cleaner lists.
- 🔔 **Tray Notifications** – Get instant alerts when monitored apps are running.
- 📋 **Quick Add/Remove** – Manage monitored applications dynamically.
- ⚙️ **Adjustable Check Interval** – Set custom scan intervals from 5 seconds to 1 hour.
- 🛠️ **Cross-Platform** – Works on Windows, macOS, and Linux (minor tweaks may be required).

---

## 🖼️ Screenshot

![App Screenshot](docs/screenshot.png)

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/app-monitor.git
cd app-monitor

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

python app_monitor.py

pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed app_monitor.py
