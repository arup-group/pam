<!---
Changelog headings can be any of:

Added: for new features.
Changed: for changes in existing functionality.
Deprecated: for soon-to-be removed features.
Removed: for now removed features.
Fixed: for any bug fixes.
Security: in case of vulnerabilities.
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Python 3.9 support (#192).
- Documentation, now available at https://arup-group.github.io/pam (#197).
- **internal** [Codecov](https://codecov.io) and [pre-commit](https://pre-commit.ci/) CI bots (#202).
- **internal** Github action job to build PAM and run tests on a Windows machine (#192).

### Changed
- Recommended installation instructions, to use [mamba](https://mamba.readthedocs.io/en/latest/index.html) instead of pip (#192).
- **internal** Source code and example notebook code layout to align with pep8 guidelines and to remove unused dependency imports (#196, #201).
- **internal** development toolkit, moving from internal scripts to pytest plugins (#193).

### Removed
- Example data files not accessed by any example notebook (#196).
- **internal** Unused scripts that were outside the source code directory (#199).

## [v0.2.4] - 2023-06-08
This version is a pre-release

### Added
- Option to skip existing facility locations during facility sampling, by adding the `location_override` argument to the `population.sample_locs` method (#190).

## [v0.2.3] - 2023-06-07
This version is a pre-release

### Fixed
- A bug when creating origin-destination (OD) matrices within the `ODFactory` class (#191).

## [v0.2.2] - 2023-05-30

### Added
- Abstract mode and location choice modules, available within the `pam.planner.choice_location` module (#189).

### Changed
- **internal** Docker base image to ensure successful CodeBuild CD pipeline builds (#188).

## [v0.2.1] - 2023-05-11

### Added
- **internal** initialisation files, such that PAM submodules can be accessed after installing the repository as a package with pip (#187).

## [v0.2.0] - 2023-05-10

This is the first version of PAM which follows semantic versioning and can be considered the first _official_ release of the package. 


[unreleased]: https://github.com/arup-group/pam/compare/v0.2.4...main
[v0.2.4]: https://github.com/arup-group/pam/compare/v0.2.3...v0.2.4
[v0.2.3]: https://github.com/arup-group/pam/compare/v0.2.2...v0.2.3
[v0.2.2]: https://github.com/arup-group/pam/compare/v0.2.1...v0.2.2
[v0.2.1]: https://github.com/arup-group/pam/compare/v0.2.0...v0.2.1
[v0.2.0]: https://github.com/arup-group/pam/compare/initial_version...v0.2.0