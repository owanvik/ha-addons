# Changelog

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
