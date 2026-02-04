# Changelog

## [1.7.2] - 2026-02-04

### Changed
- Grouped audio settings (samplerate, channels, bitrate) into collapsible "Audio Quality" section

## [1.7.1] - 2026-02-04

### Changed
- Added "(Default)" label to default options in radio buttons for clarity

## [1.7.0] - 2026-02-04

### Changed
- Improved configuration UI with dropdown selects instead of radio buttons
- Added translations for better labels and descriptions
- Password field now hides input

## [1.6.0] - 2026-02-04

### Added
- Low latency mode option to reduce stream delay (~2-3s instead of ~5-10s)
  - Reduces Icecast buffer sizes
  - Adds FFmpeg low-delay flags
  - Disabled by default (may cause stuttering on slow networks)

## [1.5.0] - 2026-02-04

### Added
- Noise reduction options with configurable audio filters:
  - Highpass filter (20-100 Hz) to remove turntable rumble
  - Lowpass filter (10000-20000 Hz) to remove hiss and high-frequency noise
  - FFT-based denoiser with adjustable strength (0.1-1.0)
- All filters are optional and disabled by default

## [1.2.0] - 2026-02-02

### Changed
- Updated FFmpeg command to match user's working configuration
- Default audio device changed to "default" (simpler)
- Added `-sample_fmt s32p` for better audio quality
- Removed `-reservoir 0` option
- Skip device check when using "default" device

## [1.1.0] - 2026-02-02

### Changed
- Replaced Darkice with FFmpeg (more portable, available in Alpine repos)
- Fixed Icecast paths for Alpine Linux
- Added clean shutdown handling

## [1.0.0] - 2026-02-02

### Added
- Initial release
- Bundled Icecast 2 server
- Bundled Darkice encoder
- Configurable station name and mount point
- Configurable audio input device
- Auto-restart on Darkice failure
- Music Assistant compatible MP3 stream
