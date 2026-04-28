@echo off
title Chatterbox Installer
color 0A

echo.
echo  ============================================
echo    CHATTERBOX  -  Live Interpreter Installer
echo  ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
        echo  Download Python 3.10+ from https://python.org
            pause
                exit /b 1
                )

                echo  [1/4] Python found. Installing dependencies...
                python -m pip install --upgrade pip --quiet
                python -m pip install -r requirements.txt

                if errorlevel 1 (
                    echo.
                        echo  [ERROR] Dependency installation failed.
                            echo  Try running as Administrator or check your internet connection.
                                pause
                                    exit /b 1
                                    )

                                    echo.
                                    echo  [2/4] Creating /tools folder for SoundVolumeView...
                                    if not exist "tools" mkdir tools
                                    echo         Place SoundVolumeView.exe inside the /tools folder.
                                    echo         Download from: https://www.nirsoft.net/utils/soundvolumeview.html

                                    echo.
                                    echo  [3/4] Checking VB-Cable installation...
                                    python -c "from audio_devices import get_all_cable_devices; d=get_all_cable_devices(); print('  CABLE A:', 'Found' if d['cable_a_input'] else 'NOT FOUND - install from vb-audio.com/Cable'); print('  CABLE B:', 'Found' if d['cable_b_input'] else 'NOT FOUND - install VB-Cable A+B from vb-audio.com/Cable')"

                                    echo.
                                    echo  [4/4] Creating desktop shortcut...
                                    set SCRIPT_DIR=%~dp0
                                    set SHORTCUT=%USERPROFILE%\Desktop\Chatterbox.lnk
                                    powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='pythonw'; $s.Arguments='%SCRIPT_DIR%main.py'; $s.WorkingDirectory='%SCRIPT_DIR%'; $s.Save()"
                                    echo         Desktop shortcut created: Chatterbox.lnk

                                    echo.
                                    echo  ============================================
                                    echo    INSTALLATION COMPLETE
                                    echo  ============================================
                                    echo.
                                    echo  Next steps:
                                    echo    1. Install VB-Cable from vb-audio.com/Cable
                                    echo    2. Install VB-Cable A+B from the same site
                                    echo    3. Place SoundVolumeView.exe in /tools folder
                                    echo    4. Reboot Windows
                                    echo    5. Double-click Chatterbox on your desktop
                                    echo.
                                    pause
