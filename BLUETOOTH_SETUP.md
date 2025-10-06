# UNIAC Bluetooth Audio Setup Guide

This guide will help you set up your UNIAC Nixie clock to work with Bluetooth audio instead of Spotify.

## Prerequisites

Your Raspberry Pi Zero W needs:
1. BlueZ (Bluetooth stack) - usually pre-installed on Raspbian/Raspberry Pi OS
2. Python D-Bus bindings
3. PulseAudio or ALSA for audio playback

## Installation Steps

### 1. Install Required Python Packages

```bash
sudo apt-get update
sudo apt-get install -y python-dbus python-gobject
```

### 2. Configure Bluetooth for Audio

Install Bluetooth audio packages:
```bash
sudo apt-get install -y bluez pulseaudio pulseaudio-module-bluetooth
```

### 3. Configure PulseAudio for System-Wide Use

Edit `/etc/pulse/system.pa` and add:
```
load-module module-bluetooth-policy
load-module module-bluetooth-discover
```

### 4. Make Device Discoverable

Create a script to make your Pi discoverable (`/home/pi/UNIAC/bt-setup.sh`):

```bash
#!/bin/bash
# Make Bluetooth discoverable and pairable
sudo bluetoothctl <<EOF
power on
discoverable on
pairable on
agent on
default-agent
EOF
```

Make it executable:
```bash
chmod +x /home/pi/UNIAC/bt-setup.sh
```

### 5. Pair Your Phone/Device

Run the setup script:
```bash
./bt-setup.sh
```

Then on your phone:
1. Go to Bluetooth settings
2. Look for "raspberrypi" (or your Pi's hostname)
3. Pair with it
4. Connect and play audio

### 6. Test Bluetooth Audio Control

Run the test script:
```bash
python /home/pi/UNIAC/BluetoothAudio.py
```

This should show if a device is connected and display current track info.

### 7. Run UNIAC with Bluetooth

```bash
python /home/pi/UNIAC/UNIAC_Bluetooth.py
```

## Button Controls

Once running, the buttons control Bluetooth playback:

### Clock Mode (default)
- **Play/Pause**: Toggle playback
- **Plus (+)**: Next track
- **Minus (-)**: Previous track
- **Mode**: Switch display modes
- **Alarm Enable**: Toggle alarm on/off
- **Snooze**: Snooze alarm when playing

### Track Status Mode
- **Play/Pause**: Toggle playback
- **Plus (+)**: Next track
- **Minus (-)**: Previous track
- **Select**: Toggle between elapsed/remaining time
- **Mode**: Switch display modes

The Nixie display will show:
- **Clock Mode**: Current time (HH:MM:SS)
- **Track Status Mode**: Track time (MM:SS) - elapsed or remaining
- **Calendar Mode**: Date (MM/DD/YY)
- **Alarm Mode**: Alarm time (HH:MM)

## Troubleshooting

### Bluetooth device won't connect
```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check Bluetooth status
sudo systemctl status bluetooth

# Make discoverable again
./bt-setup.sh
```

### No audio playing
```bash
# Check PulseAudio is running
pulseaudio --check
pulseaudio --start

# Check audio devices
pactl list sinks short
```

### Can't control playback
The phone must support AVRCP (Audio/Video Remote Control Profile). Most modern smartphones do, but some apps may not expose controls properly.

Try:
- Spotify
- Apple Music
- YouTube Music
- Most standard music players

### D-Bus errors
```bash
# Check D-Bus is running
ps aux | grep dbus

# Restart if needed
sudo systemctl restart dbus
```

## Auto-start on Boot

To make UNIAC start automatically:

```bash
# Edit crontab
crontab -e

# Add this line:
@reboot sleep 10 && python /home/pi/UNIAC/UNIAC_Bluetooth.py autostart >> /home/pi/UNIAC/uniac.log 2>&1
```

## Differences from Spotify Version

### Removed Features:
- Playlist selection/management
- Shuffle/repeat controls (handled by phone)
- Direct volume control (use phone)

### Kept Features:
- Playback controls (play/pause/next/prev)
- Track time display
- Alarm clock
- All display modes
- Button controls

### New Features:
- Works with any Bluetooth audio source
- No internet connection required (after pairing)
- Simpler setup - no API keys needed

## Notes

- Track position accuracy depends on the Bluetooth device
- Some devices don't report track duration - in that case, only elapsed time is shown
- The system tracks time locally as a fallback
- Button response may have a slight delay due to Bluetooth communication
