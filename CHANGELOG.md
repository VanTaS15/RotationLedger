# Changelog

All notable changes to this project are documented here. The format follows
Keep a Changelog, and this project uses semantic versioning.

## [1.0.0] - 2026-09-02

### Added

- `logparse` module that reads a committed `git log -p` export into commits and
  diff hunks with no git invocation.
- `entropy` module with Shannon entropy and character-class analysis.
- `detect` module with named rules: AWS access keys, private key headers,
  bearer tokens, connection strings, and generic high-entropy assignments.
- `lifetime` module reconstructing each secret's introduce, rotate, and
  still-live state along with the exposure window in days.
- `report` module producing scan, lifetime, and exposure-days reports.
