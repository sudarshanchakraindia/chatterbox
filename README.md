# Chatterbox - Real-Time Bidirectional Live Interpreter

Break language barriers in **any video call** — WhatsApp, Telegram, Zoom, Teams, Discord and more.
Both sides of the call hear each other **in their own language**, in real time.

## How It Works

```
You speak (English)      -> Chatterbox translates -> Caller hears Spanish
Caller speaks (Spanish)  -> Chatterbox translates -> You hear English
```

Works with **any app** using VB-Cable virtual audio as a transparent loopback bridge.

## Requirements

| Requirement | Cost | Link |
|---|---|---|
| Python 3.10+ | Free | python.org |
| VB-Cable | Free | vb-audio.com/Cable |
| VB-Cable A+B | Free | vb-audio.com/Cable |
| SoundVolumeView | Free | nirsoft.net/utils/soundvolumeview.html |

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/sudarshanchakraindia/chatterbox.git
cd chatterbox

# 2. Run the installer (Windows)
setup.bat

# OR install manually:
pip install -r requirements.txt
```

Then:
1. Install VB-Cable and VB-Cable A+B from vb-audio.com/Cable -> reboot
2. 2. Place SoundVolumeView.exe in the /tools folder
   3. 3. Run: `python main.py`
     
      4. ## Usage
     
      5. 1. Open your call app (WhatsApp Desktop, Telegram, Zoom...)
         2. 2. Start or join a call
            3. 3. In Chatterbox -> **Audio Setup** tab -> click **Auto-Configure**
               4. 4. Switch to **Live Interpreter** tab
                  5. 5. Select your language and the caller's language
                     6. 6. Click **Start Live Interpreter**
                        7. 7. Speak — both sides hear each other in their own language
                          
                           8. To stop: click Stop -> go to Audio Setup -> click Restore Original Devices
                          
                           9. ## File Structure
                          
                           10. ```
                               chatterbox/
                               ├── main.py                      # App entry point
                               ├── audio_devices.py             # VB-Cable device discovery
                               ├── audio_router.py              # Auto-config orchestrator
                               ├── app_detector.py              # Scans for running call apps
                               ├── win_audio_policy.py          # Windows per-app audio routing
                               ├── loopback_capture.py          # Captures incoming call audio
                               ├── bidirectional_interpreter.py # Two-way translation engine
                               ├── tts_engine.py                # Neural text-to-speech
                               ├── ui_auto_router.py            # Audio Setup tab UI
                               ├── ui_interpreter.py            # Live Interpreter tab UI
                               ├── requirements.txt             # Python dependencies
                               ├── setup.bat                    # One-click Windows installer
                               ├──
