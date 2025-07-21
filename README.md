# I can't believe it's a radio!

Python proof of concept of using EO-IC100's FM radio function.

Based on decompiled Note10 framework.

Tested on EO-IC100BBEGKR (Korean model of EO-IC100) firmware version 0.56_050401_aa

## Features

Functions working:

- Turn on/off radio
- Frequency tuning with smooth transitions
- Set volume/mute with pop sound prevention
- Get RDS data
- Station presets and scanning
- Modern GUI with device selection
- Cross-platform support (macOS, Windows)

## Audio Improvements

This enhanced version includes several improvements to reduce pop sounds:

- **Smooth Volume Control**: Gradual volume changes prevent sudden audio spikes
- **Soft Mute/Unmute**: Progressive muting reduces clicking sounds
- **Frequency Change Buffering**: Volume is temporarily lowered during frequency changes
- **Power Sequence Optimization**: Proper startup/shutdown sequences minimize pops
- **USB Communication Stability**: Retry mechanisms and timing improvements
- **Platform-Specific Tuning**: Optimized settings for macOS, Windows, and Linux

## Todos

- Add more function
- Further optimize audio transitions
- Add user-configurable audio settings

## Notes

⚠️ **Pop Sound**: While significantly reduced, occasional pop sounds may still occur due to hardware limitations. The software implements multiple mitigation strategies to minimize this issue.
