# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Sidebar with links to dates in order (to move easier throughout the document).
- Print styles: printing (or saving as PDF from the browser) hides the navigation and expands changed files.
- Thumbnails of the images (`IMAGE_EXT`) changed in a commit, if unchanged since.
- Git tags shown as milestone badges next to the commit title.
- Search box to filter commits by title, message, author, files or sha.
- `labnotebook commit` command: commits the exported notebook as `labnotebook <labnotebook@localhost>`.
- `labnotebook export --commit`: export and commit the notebook in one step.
- `export --since/--until/--branch/--path` to export part of the history.
- `IGNORE_MESSAGES` config option: commits whose title matches one of these regular expressions are excluded.
- `REMOTE_URL` config option (filled by `init` from `origin`): links commits and the file version of each commit to the remote.
- `IGNORE_AUTHORS` config option: commits by these author names/emails are excluded from the notebook (defaults to the `labnotebook commit` identity, also for existing `.labnotebookrc` files).

### Changed

- Commit dates are author dates (unchanged by rebase/amend), commits ordered by author date.
- `LAB_CSS` empty means the bundled style; custom paths are relative to the git root.
- Export output path is relative to the current folder; analysis links are relative to the notebook.
- Changed files show their git status; footer shows the pylabnotebook version.
- Requires Python >= 3.9.

### Fixed

- `ANALYSIS_IGNORE` is documented as regular expressions (as implemented); invalid patterns give a clear error instead of a traceback.
- PyYAML was not declared as a dependency; dropped argparse, setuptools and docs-only dependencies.
- Commit titles/messages are HTML-escaped; line breaks are kept.
- `ANALYSIS_EXT` matches file extensions only (`.html` no longer matches `report.html.bak`).
- Renamed files and file names with non-ASCII characters.
- Analysis files changed in later commits are flagged, since links open the current version.
- `init` works when git `user.name` is not set; error message referenced the non-existing `create` command.
- `SHOW_ANALYSIS_FILES: False` had no effect; it now hides the analysis files list.
- Export is much faster on long histories (one git call instead of three per commit).

## [0.3.1] - 2024-11-15

### Fix

- Change --link flag for export to --no-link. Default now is to have links to analysis files, to diable use --no-link flag.

## [0.3.0] - 2024-10-30

### Added

- Button to move faster from top to bottom of the notebook (useful for very long notebooks)

### Changed

- Changed the backend to Jinja2
- Changed the way how configurations are set
- From .pylabnotebook folder to a single .pylabnotebookrc config file

## [0.2.1] - 2024-09-11

### Added

- New notebook commit command that commits changes in .labnotebook folder.

### Fixed

- Remove link to non-existing analysis files (deleted or renamed in the commit).

## [0.2.0] - 2024-08-21

### Changed

- New default style for the output notebook.

### Fixed

- New behaviour for newlines in message section. It will now put a newline tag whenever it finds a newline sign from the original commit message which follows a fullstop, a question mark, an exclamation mark or a colon.
- Updated version of example page in documentation.

[unreleased]: https://github.com/mmiots9/pylabnotebook/compare/0.3.1...HEAD
[0.3.1]: https://github.com/mmiots9/pylabnotebook/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/mmiots9/pylabnotebook/compare/0.2.1...0.3.0
[0.2.1]: https://github.com/mmiots9/pylabnotebook/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/mmiots9/pylabnotebook/compare/v0.1.11..v0.2.0
