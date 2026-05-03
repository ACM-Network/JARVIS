"""
commands.py — System Command Processor for JARVIS
Handles deterministic commands that don't need AI:
  - Time and date
  - System info (CPU, RAM, battery)
  - Open applications
  - File search
  - Volume control
  - Web search / weather (via requests + BeautifulSoup)
  - Calculator
"""

import os
import re
import sys
import time
import platform
import subprocess
import webbrowser
import datetime
from utils import logger

# ── Optional dependencies (graceful fallback if missing) ──────────────────────
try:
    import psutil
    _psutil_ok = True
except ImportError:
    _psutil_ok = False

try:
    import requests
    from bs4 import BeautifulSoup
    _web_ok = True
except ImportError:
    _web_ok = False
    logger.warning("requests/BeautifulSoup not installed. Web features disabled.")
    logger.warning("Run: pip install requests beautifulsoup4")

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    _pycaw_ok = True
except Exception:
    _pycaw_ok = False

_OS = platform.system()  # "Windows", "Linux", "Darwin"


class CommandProcessor:
    """
    Matches user input against known command patterns.
    Returns a response string, or None if no command matched
    (so the caller can escalate to the AI brain).
    """

    def process(self, text: str) -> str | None:
        """
        Try every handler in priority order.
        Returns response string on match, None if nothing matched.
        """
        text_lower = text.lower().strip()

        handlers = [
            self._handle_time,
            self._handle_date,
            self._handle_system_info,
            self._handle_battery,
            self._handle_volume,
            self._handle_calculator,
            self._handle_open_app,
            self._handle_weather,
            self._handle_web_search,
            self._handle_file_search,
            self._handle_screenshot,
        ]

        for handler in handlers:
            result = handler(text_lower, text)
            if result is not None:
                return result

        return None  # No command matched — caller will use AI brain

    # ── Time & Date ───────────────────────────────────────────────────────────

    def _handle_time(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(time|clock|what time)\b", text):
            return None
        now = datetime.datetime.now()
        hour = now.strftime("%I").lstrip("0") or "12"
        return f"The current time is {hour}:{now.strftime('%M')} {now.strftime('%p')}, Sir."

    def _handle_date(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(date|today|day|month|year)\b", text):
            return None
        now = datetime.datetime.now()
        day  = now.strftime("%A")
        date = now.strftime("%B %d, %Y")
        return f"Today is {day}, {date}, Sir."

    # ── System Info ───────────────────────────────────────────────────────────

    def _handle_system_info(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(system info|cpu|processor|memory|ram|system status)\b", text):
            return None
        if not _psutil_ok:
            os_name = platform.system()
            return (f"Running on {os_name}. "
                    "Install psutil for detailed system information, Sir.")
        cpu   = psutil.cpu_percent(interval=0.5)
        ram   = psutil.virtual_memory()
        used  = round(ram.used  / (1024**3), 1)
        total = round(ram.total / (1024**3), 1)
        pct   = ram.percent
        return (f"CPU usage is at {cpu}%. "
                f"RAM: {used} GB used of {total} GB — {pct}% utilised, Sir.")

    def _handle_battery(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(battery|charge|charging)\b", text):
            return None
        if not _psutil_ok:
            return "Please install psutil for battery information, Sir."
        bat = psutil.sensors_battery()
        if bat is None:
            return "No battery detected. You appear to be on a desktop system, Sir."
        pct = round(bat.percent)
        status = "charging" if bat.power_plugged else "on battery"
        time_left = ""
        if bat.secsleft > 0 and not bat.power_plugged:
            hrs  = bat.secsleft // 3600
            mins = (bat.secsleft % 3600) // 60
            time_left = f" Approximately {hrs} hours and {mins} minutes remaining."
        return f"Battery is at {pct}%, currently {status}, Sir.{time_left}"

    # ── Volume Control ────────────────────────────────────────────────────────

    def _handle_volume(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(volume|mute|unmute|louder|quieter|sound)\b", text):
            return None

        if _OS == "Windows" and _pycaw_ok:
            return self._windows_volume(text)
        elif _OS == "Linux":
            return self._linux_volume(text)
        elif _OS == "Darwin":
            return self._mac_volume(text)
        return "Volume control is not supported on your system, Sir."

    def _windows_volume(self, text: str) -> str:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            if "mute" in text:
                volume.SetMute(1, None)
                return "Audio muted, Sir."
            if "unmute" in text:
                volume.SetMute(0, None)
                return "Audio unmuted, Sir."
            match = re.search(r"(\d+)\s*(?:percent|%)?", text)
            if match:
                level = max(0, min(100, int(match.group(1)))) / 100
                volume.SetMasterVolumeLevelScalar(level, None)
                return f"Volume set to {int(level*100)}%, Sir."
        except Exception as e:
            logger.error(f"Windows volume error: {e}")
        return "I was unable to adjust the volume, Sir."

    def _linux_volume(self, text: str) -> str:
        if "mute" in text and "unmute" not in text:
            os.system("amixer -q set Master mute")
            return "Audio muted, Sir."
        if "unmute" in text:
            os.system("amixer -q set Master unmute")
            return "Audio unmuted, Sir."
        match = re.search(r"(\d+)\s*(?:percent|%)?", text)
        if match:
            level = max(0, min(100, int(match.group(1))))
            os.system(f"amixer -q set Master {level}%")
            return f"Volume set to {level}%, Sir."
        if "louder" in text or "increase" in text or "up" in text:
            os.system("amixer -q set Master 10%+")
            return "Volume increased, Sir."
        if "quieter" in text or "decrease" in text or "down" in text:
            os.system("amixer -q set Master 10%-")
            return "Volume decreased, Sir."
        return "I'm not sure how to adjust the volume. Try 'set volume to 50 percent'."

    def _mac_volume(self, text: str) -> str:
        match = re.search(r"(\d+)\s*(?:percent|%)?", text)
        if match:
            level = max(0, min(100, int(match.group(1))))
            os.system(f"osascript -e 'set volume output volume {level}'")
            return f"Volume set to {level}%, Sir."
        if "mute" in text:
            os.system("osascript -e 'set volume output muted true'")
            return "Audio muted, Sir."
        if "unmute" in text:
            os.system("osascript -e 'set volume output muted false'")
            return "Audio unmuted, Sir."
        return "Please specify a volume level, Sir. For example, 'set volume to 60 percent'."

    # ── Calculator ────────────────────────────────────────────────────────────

    def _handle_calculator(self, text: str, _raw: str) -> str | None:
        if not re.search(
            r"\b(calculate|what is|compute|how much is|plus|minus|times|divided)\b",
            text
        ):
            return None

        # Extract a math expression
        # Replace spoken words with operators
        expr = (text
                .replace("plus",      "+")
                .replace("minus",     "-")
                .replace("times",     "*")
                .replace("multiplied by", "*")
                .replace("divided by",    "/")
                .replace("percent of",   "* 0.01 *"))

        # Keep only valid math characters
        expr = re.sub(r"[^0-9+\-*/().\s]", "", expr).strip()
        if not expr:
            return None

        try:
            result = eval(expr, {"__builtins__": {}})  # safe eval with no builtins
            result = round(float(result), 6)
            # Display nicely: int if possible
            if result == int(result):
                result = int(result)
            return f"The result is {result}, Sir."
        except Exception:
            return None  # Not a valid math expression — let brain handle it

    # ── Open Applications ─────────────────────────────────────────────────────

    # Map of spoken names to executable names / commands
    APP_MAP = {
        "chrome":     {"Windows": "chrome",         "Linux": "google-chrome", "Darwin": "Google Chrome"},
        "firefox":    {"Windows": "firefox",         "Linux": "firefox",       "Darwin": "Firefox"},
        "notepad":    {"Windows": "notepad",         "Linux": "gedit",         "Darwin": "TextEdit"},
        "calculator": {"Windows": "calc",            "Linux": "gnome-calculator", "Darwin": "Calculator"},
        "terminal":   {"Windows": "cmd",             "Linux": "gnome-terminal","Darwin": "Terminal"},
        "file manager":{"Windows":"explorer",        "Linux": "nautilus",      "Darwin": "Finder"},
        "settings":   {"Windows": "ms-settings:",   "Linux": "gnome-control-center", "Darwin": "System Preferences"},
        "task manager":{"Windows":"taskmgr",         "Linux": "gnome-system-monitor", "Darwin": "Activity Monitor"},
        "music":      {"Windows": "wmplayer",        "Linux": "rhythmbox",     "Darwin": "Music"},
        "paint":      {"Windows": "mspaint",         "Linux": "pinta",         "Darwin": ""},
        "word":       {"Windows": "winword",         "Linux": "libreoffice --writer", "Darwin": ""},
        "excel":      {"Windows": "excel",           "Linux": "libreoffice --calc",   "Darwin": ""},
        "vlc":        {"Windows": "vlc",             "Linux": "vlc",           "Darwin": "VLC"},
        "vscode":     {"Windows": "code",            "Linux": "code",          "Darwin": "Visual Studio Code"},
    }

    def _handle_open_app(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(open|launch|start|run)\b", text):
            return None

        for app_name, os_cmds in self.APP_MAP.items():
            if app_name in text:
                cmd = os_cmds.get(_OS, "")
                if not cmd:
                    return f"I don't know how to open {app_name} on your system, Sir."
                try:
                    if _OS == "Windows":
                        if cmd.endswith(":"):   # protocol URL like ms-settings:
                            os.startfile(cmd)
                        else:
                            subprocess.Popen(cmd, shell=True)
                    elif _OS == "Darwin":
                        subprocess.Popen(["open", "-a", cmd])
                    else:  # Linux
                        subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                    return f"Opening {app_name}, Sir."
                except Exception as e:
                    logger.error(f"Failed to open {app_name}: {e}")
                    return f"I was unable to open {app_name}, Sir. It may not be installed."

        return None  # No app keyword matched

    # ── Weather (free, no API key via wttr.in) ─────────────────────────────────

    def _handle_weather(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(weather|temperature|forecast)\b", text):
            return None

        # Extract city name: "weather in London" or "London weather"
        city = None
        m = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", text)
        if m:
            city = m.group(1).strip().title()
        else:
            m = re.search(r"([a-zA-Z\s]+)\s+weather", text)
            if m:
                city = m.group(1).strip().title()

        if not city:
            return ("Please specify a city, Sir. "
                    "For example: 'weather in London'.")

        if not _web_ok:
            return ("Web features are not available. "
                    "Install requests and beautifulsoup4, Sir.")

        return self._fetch_weather(city)

    def _fetch_weather(self, city: str) -> str:
        """Fetch weather from wttr.in (100% free, no API key)."""
        try:
            url = f"https://wttr.in/{city}?format=3"
            headers = {"User-Agent": "JARVIS/1.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                # Response looks like: "London: 🌦 +18°C"
                # Strip the emoji for cleaner speech
                raw = resp.text.strip()
                clean = re.sub(r"[^\x00-\x7F]+", "", raw).strip()
                clean = re.sub(r"\s+", " ", clean)
                return f"The current weather in {city}: {clean}, Sir."
            return f"I could not retrieve weather data for {city}, Sir."
        except requests.exceptions.ConnectionError:
            return "No internet connection available, Sir. Weather unavailable."
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return f"I encountered an error fetching the weather, Sir."

    # ── Web Search ────────────────────────────────────────────────────────────

    def _handle_web_search(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(search|google|look up|find information|search for)\b", text):
            return None

        # Extract the search query
        query = re.sub(
            r"\b(search|google|look up|find information about|search for|on the web|online)\b",
            "", text, flags=re.IGNORECASE
        ).strip()

        if not query:
            return "What would you like me to search for, Sir?"

        if not _web_ok:
            # Open browser as fallback
            encoded = query.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={encoded}")
            return f"Opening browser search for '{query}', Sir."

        return self._duckduckgo_search(query)

    def _duckduckgo_search(self, query: str) -> str:
        """Scrape DuckDuckGo for an instant answer (free, no API key)."""
        try:
            encoded = query.replace(" ", "+")
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}
            resp = requests.get(url, headers=headers, timeout=6)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to get the instant answer / snippet
            instant = soup.find("div", class_="zci__body")
            if instant:
                text = instant.get_text(" ", strip=True)[:300]
                return f"Here is what I found, Sir: {text}"

            # Fall back to first result snippet
            snippets = soup.find_all("a", class_="result__snippet")
            if snippets:
                text = snippets[0].get_text(" ", strip=True)[:250]
                return f"According to my search: {text}"

            # Last resort — open browser
            webbrowser.open(f"https://www.google.com/search?q={encoded}")
            return (f"I couldn't extract a direct answer. "
                    f"I've opened your browser to search for '{query}', Sir.")

        except requests.exceptions.ConnectionError:
            return "No internet connection available, Sir."
        except Exception as e:
            logger.error(f"Search error: {e}")
            return "My search systems encountered an error, Sir."

    # ── File Search ───────────────────────────────────────────────────────────

    def _handle_file_search(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(find file|search file|locate file|where is file|find my)\b", text):
            return None

        m = re.search(
            r"\b(?:find|search|locate|where is)\s+(?:file\s+)?[\"']?([a-zA-Z0-9_.\-\s]+)[\"']?",
            text
        )
        if not m:
            return "Please tell me the filename to search for, Sir."

        filename = m.group(1).strip()
        return self._search_file(filename)

    def _search_file(self, filename: str) -> str:
        """Search common user directories for a file."""
        search_dirs = []

        home = os.path.expanduser("~")
        for d in ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]:
            path = os.path.join(home, d)
            if os.path.isdir(path):
                search_dirs.append(path)

        found = []
        for directory in search_dirs:
            for root, _, files in os.walk(directory):
                for f in files:
                    if filename.lower() in f.lower():
                        found.append(os.path.join(root, f))
                        if len(found) >= 3:
                            break

        if not found:
            return f"I could not find any file matching '{filename}' in your common directories, Sir."
        if len(found) == 1:
            return f"Found it, Sir. The file is at: {found[0]}"
        paths = ", ".join(found[:3])
        return f"I found {len(found)} matching files, Sir. The first few: {paths}"

    # ── Screenshot ────────────────────────────────────────────────────────────

    def _handle_screenshot(self, text: str, _raw: str) -> str | None:
        if not re.search(r"\b(screenshot|screen capture|capture screen)\b", text):
            return None

        try:
            import PIL.ImageGrab as ImageGrab
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = os.path.join(os.path.expanduser("~"), "Desktop",
                                     f"jarvis_screenshot_{timestamp}.png")
            img = ImageGrab.grab()
            img.save(filename)
            return f"Screenshot saved to your Desktop as jarvis_screenshot_{timestamp}.png, Sir."
        except ImportError:
            return "Please install Pillow to use screenshot functionality. Run: pip install Pillow"
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return "I was unable to take a screenshot, Sir."
