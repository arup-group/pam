<!---
Changelog headings can be any of:

Added: for new features.
Changed: for changes in existing functionality.
Deprecated: for soon-to-be removed features.
Removed: for now removed features.
Fixed: for any bug fixes.
Security: in case of vulnerabilities.

Release headings should be of the form:
## [X.Y.Z] - YEAR-MONTH-DAY
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed


### Added

- Python version 3.12 support
- Support for `geopandas` v0.15, `gdal` >= v3.5, and `python-Levenshtein` v0.26 ([#268]).

### Changed

- **internal** Align project to the [CML cookiecutter template](https://github.com/arup-group/cookiecutter-pypackage/) and track it with a Cruft config and CI job.

## [v0.3.1] - 2023-11-07

### Fixed

- **internal** conda upload CI script.
- **public** fix person attributes type conversion bug ([#263](https://github.com/arup-group/pam/issues/263))

### Added

- **internal** PyPI build and upload CI scripts (triggered on tagging and releasing new versions).

### Changed

- User install instructions to prefer direct install from mamba (or PyPI if a user is willing to deal with installing non-python libs themselves).

## [v0.3.0] - 2023-09-27

### Fixed

- readme CI badge ([#248])
- plan cropping as per issue [#241] ([#240]).
- [][pam.optimise.grid.grid_search] ([#239]).
- [`TourPlanner`][pam.samplers.tour.TourPlanner] prevents sampling of duplicate destinations, and prevents origin being sampled as a destination ([#231]).
- [][pam.activity.Plan.simplify_pt_trips] as per issue [#221], improving "pt simplification" ([#222])
- Slow loading of data with e.g., [pam.read.load_travel_diary][pam.read.diary.load_travel_diary] when using pandas v2.1.1 (caused by `pandas.MultiIndex.groupby`, see [pandas issue #55256](https://github.com/pandas-dev/pandas/issues/55256)). ([#258])

### Added

- MATSim warm starting example ([#239]).
- Support for MATSim vehicles files ([#215]).
- Anaconda package of PAM, available on the `city-modelling-lab` channel ([#211]).
- Python versions 3.9 to 3.11 support ([#192], [#210]).
- Documentation, now available at <https://arup-group.github.io/pam> ([#197]).
- Time-space prism method for selecting the location of non-mandatory activities ([#252]).
- Simple IPF approach for generating synthetic populations ([#253]).
- More control over the look of activity plan plots, with keyword arguments for [][pam.plot.plot_activities] (accessed via e.g. [pam.core.Person.plot]) extended to allow figure width and per-activity label font sizes to be updated ([#249]).
- **internal** [Codecov](https://codecov.io) and [pre-commit](https://pre-commit.ci/) CI bots ([#202]).
- **internal** Github action job to build PAM and run tests on Windows and MacOS machines ([#192]).
- **internal** Contribution guidelines and issue/pull request templates ([#207]).

### Changed

- Documentation and examples improved ([#239]).
- [`TourPlanner`][pam.samplers.tour.TourPlanner] class sequences stops using GreedyTSP algorithm, rather than previous method sorting by distance from depot ([#231]).
- Minor changes to docs for zsh users (eg `pip install '.[dev]'`)([#219]).
- Recommended installation instructions, to use [mamba](https://mamba.readthedocs.io/en/latest/index.html) instead of pip ([#192], [#211]).
- Docker image entry point from python to bash ([#230]).
- **internal** Source code and example notebook code layout to align with pep8 guidelines and to remove unused dependency imports ([#196], [#201]).
- **internal** Docstrings to Google style ([#208])
- **internal** development toolkit, moving from internal scripts to pytest plugins ([#193]).
- **internal** CI actions link to reusable ones from `arup-group/actions-city-modelling-lab/`, including new memory profiling and multi-OS / python version tests ([#243]).

### Removed

- Example data files not accessed by any example notebook ([#196]).
- `ActivityDuration` class, replaced with methods in [`TourPlanner`][pam.samplers.tour.TourPlanner] and in `pam.samplers.tour` ([#231]).
- **internal** Unused scripts that were outside the source code directory ([#199]).

## [v0.2.4] - 2023-06-08

This version is a pre-release

### Added

- Option to skip existing facility locations during facility sampling, by adding the `location_override` argument to the [`sample_locs`][pam.core.Population.sample_locs] method ([#190]).

## [v0.2.3] - 2023-06-07

This version is a pre-release

### Fixed

- A bug when creating origin-destination (OD) matrices within the `ODFactory` class ([#191]).

## [v0.2.2] - 2023-05-30

### Added

- Abstract mode and location choice modules, available within the `pam.planner.choice_location` module ([#189]).

### Changed

- **internal** Docker base image to ensure successful CodeBuild CD pipeline builds ([#188]).

## [v0.2.1] - 2023-05-11

### Added

- **internal** initialisation files, such that PAM submodules can be accessed after installing the repository as a package with pip ([#187]).

## [v0.2.0] - 2023-05-10

This is the first version of PAM which follows semantic versioning and can be considered the first _official_ release of the package.

[Unreleased]: https://github.com/arup-group/pam/compare/v0.3.1...main
[v0.3.1]: https://github.com/arup-group/pam/compare/v0.3.0...v0.3.1
[v0.3.0]: https://github.com/arup-group/pam/compare/v0.2.4...v0.3.0
[v0.2.4]: https://github.com/arup-group/pam/compare/v0.2.3...v0.2.4
[v0.2.3]: https://github.com/arup-group/pam/compare/v0.2.2...v0.2.3
[v0.2.2]: https://github.com/arup-group/pam/compare/v0.2.1...v0.2.2
[v0.2.1]: https://github.com/arup-group/pam/compare/v0.2.0...v0.2.1
[v0.2.0]: https://github.com/arup-group/pam/compare/initial_version...v0.2.0

[#268]: https://github.com/arup-group/pam/pull/268
[#258]: https://github.com/arup-group/pam/pull/258
[#253]: https://github.com/arup-group/pam/pull/253
[#252]: https://github.com/arup-group/pam/pull/252
[#249]: https://github.com/arup-group/pam/pull/249
[#248]: https://github.com/arup-group/pam/pull/248
[#241]: https://github.com/arup-group/pam/issues/241
[#240]: https://github.com/arup-group/pam/pull/240
[#239]: https://github.com/arup-group/pam/pull/239
[#231]: https://github.com/arup-group/pam/pull/231
[#230]: https://github.com/arup-group/pam/pull/230
[#243]: https://github.com/arup-group/pam/pull/243
[#222]: https://github.com/arup-group/pam/pull/222
[#221]: https://github.com/arup-group/pam/issues/221
[#219]: https://github.com/arup-group/pam/pull/219
[#215]: https://github.com/arup-group/pam/pull/215
[#211]: https://github.com/arup-group/pam/pull/211
[#210]: https://github.com/arup-group/pam/pull/210
[#208]: https://github.com/arup-group/pam/pull/208
[#207]: https://github.com/arup-group/pam/pull/207
[#202]: https://github.com/arup-group/pam/pull/202
[#201]: https://github.com/arup-group/pam/pull/201
[#199]: https://github.com/arup-group/pam/pull/199
[#197]: https://github.com/arup-group/pam/pull/197
[#196]: https://github.com/arup-group/pam/pull/196
[#193]: https://github.com/arup-group/pam/pull/193
[#192]: https://github.com/arup-group/pam/pull/192
[#191]: https://github.com/arup-group/pam/pull/191
[#190]: https://github.com/arup-group/pam/pull/190
[#189]: https://github.com/arup-group/pam/pull/189
[#188]: https://github.com/arup-group/pam/pull/188
[#187]: https://github.com/arup-group/pam/pull/187
