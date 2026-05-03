# 🤖 JARVIS — Just A Rather Very Intelligent System

A real-life offline AI assistant inspired by J.A.R.V.I.S. from Marvel.  
**100% free. No API keys. No subscriptions. Works on low-end laptops.**

---

## 📁 Project Structure

```
jarvis/
├── main.py          — Entry point: wake word loop → command → AI response
├── voice.py         — Speech-to-text (Vosk) + Text-to-speech (pyttsx3)
├── brain.py         — AI brain: Ollama LLM + rule-based fallback
├── commands.py      — System commands: time, weather, apps, volume, search
├── utils.py         — Logger + banner display
├── text_mode.py     — Keyboard-only mode (no mic/speaker needed for testing)
├── requirements.txt — Python dependencies
└── models/          — Put your Vosk model folder here
    └── vosk-model/  ← rename your downloaded model to this
```

---

## 🚀 Installation Guide (Step by Step)

### Step 1 — Install Python
- Download Python 3.10 or newer from https://python.org/downloads
- During installation, check ✅ **"Add Python to PATH"**
- Verify: open a terminal and type `python --version`

### Step 2 — Download this project
Either clone with Git or download as ZIP:
```bash
git clone https://github.com/yourname/jarvis
cd jarvis
```
Or manually create the folder and copy all the files into it.

### Step 3 — Install Python packages
Open a terminal **inside the jarvis folder** and run:
```bash
pip install -r requirements.txt
```

If you're on **Windows** and want volume control, also run:
```bash
pip install pycaw
```

### Step 4 — Download the Vosk Speech Model
Vosk converts your voice to text entirely offline.

1. Go to: https://alphacephei.com/vosk/models
2. Download **vosk-model-small-en-us-0.15** (about 40 MB — fast, works on any laptop)
   - For better accuracy, download **vosk-model-en-us-0.22** (~1.8 GB) instead
3. Extract the ZIP file
4. **Rename the extracted folder to `vosk-model`**
5. Move it into the `models/` folder inside your jarvis directory

Your folder structure should look like:
```
jarvis/
└── models/
    └── vosk-model/
        ├── am/
        ├── conf/
        ├── graph/
        └── ...
```

### Step 5 (Optional but Recommended) — Install Ollama for AI brain
Ollama runs large language models locally, for free.

1. Download from: https://ollama.com
2. Install and run Ollama
3. Open a new terminal and pull a small model:
   ```bash
   ollama pull phi3:mini
   ```
   This downloads a ~2 GB model that runs on 4–8 GB RAM.
   
   For very low-end laptops (less than 4 GB RAM), try:
   ```bash
   ollama pull tinyllama
   ```

4. Verify Ollama is running: `ollama list`

If you skip this step, JARVIS uses the built-in rule-based brain instead — still works!

---

## ▶️ How to Run

### Full voice mode (microphone + speakers):
```bash
python main.py
```
- Wait for the "All systems online" message
- Say **"Jarvis"** to wake it up
- Then say your command

### Text mode (no microphone needed — great for testing):
```bash
python text_mode.py
```
- Just type commands and press Enter

---

## 🗣️ Example Commands

| You say...                        | JARVIS responds...                         |
|-----------------------------------|--------------------------------------------|
| "What time is it?"                | "The current time is 3:45 PM, Sir."        |
| "What's today's date?"            | "Today is Tuesday, January 14, 2025, Sir." |
| "Open Chrome"                     | Opens Google Chrome                        |
| "Open notepad"                    | Opens Notepad / Text Editor                |
| "System info"                     | CPU %, RAM usage                           |
| "Battery status"                  | Battery percentage and time remaining      |
| "Weather in London"               | Current London weather (needs internet)    |
| "What is 245 times 37?"           | "The result is 9065, Sir."                 |
| "Set volume to 50 percent"        | Adjusts system volume to 50%              |
| "Search for Python tutorials"     | Searches and gives a summary              |
| "Find file report.pdf"            | Searches your common folders              |
| "Tell me a joke"                  | Delivers a tech joke                       |
| "Who are you?"                    | Introduces itself as JARVIS               |

---

## 🔧 Troubleshooting

**"vosk model not found" error**
→ Make sure the model folder is at `jarvis/models/vosk-model/`

**No sound output**
→ Check your system speakers/headphones are connected
→ Try: `python -c "import pyttsx3; e=pyttsx3.init(); e.say('test'); e.runAndWait()"`

**Ollama not connecting**
→ Make sure the Ollama app is running (check system tray on Windows/Mac)
→ Run `ollama serve` in a terminal

**"pip is not recognized"**
→ Reinstall Python and check "Add to PATH" during setup

**Microphone not detected**
→ Use `text_mode.py` while debugging
→ Check your OS microphone permissions

---

## 🔮 Future Improvements

| Feature | How to add |
|---------|-----------|
| GUI interface | Use PyQt6 or Tkinter for a visual HUD |
| Custom wake word | Use Porcupine (free tier) for more accuracy |
| Smart home control | Add Home Assistant API integration |
| Email reading | Use imaplib (built-in Python) |
| Reminders / calendar | Use local SQLite + datetime scheduling |
| Face recognition | Use face_recognition library |
| Spotify control | Use spotipy (Spotify free API) |
| News briefing | RSS feed parsing with feedparser |

---

## 📄 License
MIT License — free to use, modify, and distribute.
