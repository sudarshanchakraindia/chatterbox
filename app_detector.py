"""
app_detector.py
Detects running communication/video-call applications and maps
them to their executable names for audio device assignment.
pip install psutil
"""

import psutil
from dataclasses import dataclass


@dataclass
class DetectedApp:
    display_name: str
    exe_name: str
    pid: int
    is_running: bool
    icon: str


SUPPORTED_APPS = [
    {"display": "WhatsApp Desktop",  "exe": "WhatsApp.exe",         "icon": ""},
    {"display": "WhatsApp (Store)",  "exe": "WhatsAppDesktop.exe",  "icon": ""},
    {"display": "Telegram",          "exe": "Telegram.exe",         "icon": ""},
    {"display": "Zoom",              "exe": "Zoom.exe",             "icon": ""},
    {"display": "Microsoft Teams",   "exe": "Teams.exe",            "icon": ""},
    {"display": "Teams (new)",       "exe": "ms-teams.exe",         "icon": ""},
    {"display": "Discord",           "exe": "Discord.exe",          "icon": ""},
    {"display": "Skype",             "exe": "Skype.exe",            "icon": ""},
    {"display": "Slack",             "exe": "slack.exe",            "icon": ""},
    {"display": "Google Chrome",     "exe": "chrome.exe",           "icon": ""},
    {"display": "Microsoft Edge",    "exe": "msedge.exe",           "icon": ""},
    {"display": "Mozilla Firefox",   "exe": "firefox.exe",          "icon": ""},
    {"display": "Viber",             "exe": "Viber.exe",            "icon": ""},
    {"display": "Signal",            "exe": "Signal.exe",           "icon": ""},
    {"display": "LINE",              "exe": "LINE.exe",             "icon": ""},
    {"display": "WeChat",            "exe": "WeChat.exe",           "icon": ""},
    {"display": "Webex",             "exe": "CiscoWebexStart.exe",  "icon": ""},
]


def get_running_processes() -> dict:
    running = {}
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name:
                running[name.lower()] = proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return running


def detect_communication_apps() -> list:
    running = get_running_processes()
    results = []
    seen_exes = set()
    for app in SUPPORTED_APPS:
        exe_lower = app["exe"].lower()
        if exe_lower in seen_exes:
            continue
        pid = running.get(exe_lower)
        if pid:
            seen_exes.add(exe_lower)
            results.append(DetectedApp(
                display_name=app["display"],
                exe_name=app["exe"],
                pid=pid or 0,
                is_running=pid is not None,
                icon=app["icon"],
            ))
    return results


def detect_running_apps_only() -> list:
    return [a for a in detect_communication_apps() if a.is_running]
