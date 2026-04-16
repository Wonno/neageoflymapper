# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.9] - 2026-04-16

### Added

- New CLI parameter `--bookmarklet` to set up a bookmarklet for extracting image IDs from the NEA viewer.

## [0.1.8] - 2026-04-12

### Added

- New CLI parameter `--output-dir` to specify the destination directory for downloaded files.
- New CLI parameter `--filename-template` to customize the naming convention of downloaded files using placeholders.  
- New CLI parameter `--no-download` to skip the download and composing of images tiles
- New CLI parameter `--no-kml` to skip storage of KML files
- New CLI parameter `--no-txt` to skip storage of TXT files

### Fixed
- application version is now correctly displayed in the help message.

### Changed

- Poetry update
- Exit program if no Image ID is entered in interactive mode.
- Improved error message for invalid Image IDs.

## [0.1.7] - 2026-04-01

### Added

- Added a bookmarklet-based workflow for extracting image IDs from the NEA viewer.

### Changed

- Significantly improved download speed.

