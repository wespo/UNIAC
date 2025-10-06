# Migration from Spotify to Bluetooth Audio

## Summary of Changes

This migration replaces the Spotify-based audio system with Bluetooth audio control, removing external dependencies while maintaining core functionality.

## New Files Created

1. **BluetoothAudio.py** - Core Bluetooth audio control class
   - Interfaces with BlueZ via D-Bus
   - Handles AVRCP commands (play/pause/next/previous)
   - Tracks playback time locally
   - Compatible with existing code structure

2. **UNIAC_Bluetooth.py** - Updated main program
   - Replaces Spotify/MPD with Bluetooth
   - Simplified menu structure (removed playlist selection)
   - All button controls still work
   - All display modes preserved

3. **test_bluetooth.py** - Testing utility
   - Verify Bluetooth connection
   - Test metadata retrieval
   - Test playback controls
   - Diagnostic information

4. **BLUETOOTH_SETUP.md** - Setup instructions
   - Installation steps
   - Configuration guide
   - Troubleshooting tips
   - Auto-start instructions

## Files Modified

None - the original UNIAC.py remains untouched. You can switch between versions by running different files.

## Files No Longer Needed (Spotify Version)

When you're ready to fully migrate, these can be removed:
- `spotipyLogin.py` (if it exists)
- Any Spotify API credentials
- `MPDClientBlocking.py` (if no longer using MPD)
- `mpdGeneral.py` (if it exists as separate file)

## Key Architecture Changes

### Before (Spotify):
```
UNIAC.py
  └─ spotipyLogin (Spotify API)
      └─ mpdGeneral (MPD client)
          └─ Music control via network API
```

### After (Bluetooth):
```
UNIAC_Bluetooth.py
  └─ BluetoothAudio (D-Bus)
      └─ BlueZ/AVRCP
          └─ Direct Bluetooth control
```

## Feature Comparison

### Removed Features
- ❌ Playlist selection and management
- ❌ Shuffle/repeat toggle (controlled by phone now)
- ❌ Volume control via device (use phone)
- ❌ Search and browse
- ❌ Requires Spotify account
- ❌ Requires internet connection for control

### Retained Features
- ✓ Play/Pause control
- ✓ Next/Previous track
- ✓ Track time display (elapsed/remaining)
- ✓ All button controls
- ✓ All display modes (clock, calendar, alarm, status, IP)
- ✓ Alarm functionality
- ✓ 12/24 hour mode
- ✓ Anti-cathode poisoning

### New Advantages
- ✓ Works with any Bluetooth audio source
- ✓ No API keys or accounts needed
- ✓ No internet required (after pairing)
- ✓ Simpler setup and maintenance
- ✓ Works with any music app on phone
- ✓ Lower latency for button controls

## Button Mapping (Unchanged)

| Button | Pin | Function |
|--------|-----|----------|
| Play/Pause | 3 | Toggle playback |
| Plus | 5 | Next track |
| Minus | 6 | Previous track |
| Select | 2 | Toggle elapsed/remaining time |
| Mode | 4 | Switch display modes |
| Snooze | 1 | Snooze alarm |
| Alarm Enable | 0 | Toggle alarm on/off |

## Display Modes (Unchanged)

1. **Clock Mode** - Shows current time with playback controls
2. **Audio Status Mode** - Shows track elapsed/remaining time
3. **Calendar Mode** - Shows current date
4. **Alarm Mode** - Set and display alarm time
5. **IP Address Mode** - Shows device IP
6. **Options Mode** - Configure 12/24hr and cathode protection

## Switching Between Versions

### Run Spotify Version:
```bash
python /home/pi/UNIAC/UNIAC.py
```

### Run Bluetooth Version:
```bash
python /home/pi/UNIAC/UNIAC_Bluetooth.py
```

Both versions can coexist. Test the Bluetooth version thoroughly before removing Spotify.

## Testing Checklist

Before fully migrating, test:

- [ ] Bluetooth device pairs and connects
- [ ] Audio plays through speaker
- [ ] Play/Pause button works
- [ ] Next track button works
- [ ] Previous track button works
- [ ] Track time displays correctly
- [ ] Elapsed/remaining time toggle works
- [ ] Mode switching works
- [ ] Alarm functionality works
- [ ] All display modes work
- [ ] System survives reboot

## Rollback Plan

If you encounter issues:

1. The original UNIAC.py is untouched
2. Simply run the original file to revert
3. No configuration changes affect the Spotify version
4. Both versions use the same UNIAC.conf file safely

## Next Steps

1. **Install dependencies** (see BLUETOOTH_SETUP.md)
2. **Pair Bluetooth device** to your Raspberry Pi
3. **Run test script**: `python test_bluetooth.py`
4. **Test new version**: `python UNIAC_Bluetooth.py`
5. **Update auto-start** (if satisfied with testing)
6. **Remove old dependencies** (optional, when confident)

## Support

The Bluetooth version uses standard Linux BlueZ stack and AVRCP protocol. Most issues can be resolved by:
- Restarting Bluetooth service: `sudo systemctl restart bluetooth`
- Re-pairing device
- Checking D-Bus is running: `ps aux | grep dbus`
- Verifying PulseAudio: `pulseaudio --check`

## Code Organization

The new code maintains the same class structure:
- `btAudioGeneral` replaces `mpdGeneral`
- `alarmGeneral` inherits from `btAudioGeneral`
- All display mode classes remain structurally identical
- Menu system unchanged
- Button handling unchanged

This makes future maintenance easier and keeps the learning curve minimal.
