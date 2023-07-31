# Population Activity Modeller (PAM)

![CIbadge](https://github.com/arup-group/pam//workflows/CI/badge.svg) 
[![](https://github.com/arup-group/pam/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages)](https://arup-group.github.io/pam)
[![image](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/arupcitymodelling/pandemic-activity-modifier-intro-3d2dccbc716e)

<!--- the "--8<--" html comments define what part of the README to add to the index page of the documentation -->
<!--- --8<-- [start:docs] -->

PAM is a python API for activity sequence modelling. Primary features:

- common format read/write including MATSim xml
- sequence inference from travel diary data
- rules based sequence modification
- sequence visualisation
- facility sampling
- research extensions

PAM was originally called the "Pandemic Activity Modifier". It was built in response to COVID-19, to better and more quickly update models for behaviour changes from lockdown policies than existing aggregate models.

 ![PAM](resources/PAM-motivation.png)

**Who is this for?** PAM is intended for use by any modeller or planner using trip diary data or activity plans.
**What can this do?** PAM provides an API and examples for modifying activity plans, for example, based on COVID-19 lockdown scenarios.

## Features

This project is not a new activity model. Instead it to seeks to adjust existing activity
representations, already derived from exiting models or survey data:

![PAM](resources/PAM-features.png)

(i) **Read/Load** input data (eg travel diary) to household and person Activity Plans.

(ii) **Modify** the Activity Plans for new social and government policy scenarios (eg
remove education activities for non key worker households). Crucially PAM facilitates
application of detailed policies at the person and household level, while still respecting
the logic of arbitrarily complex activity chains.

(iii) **Output** to useful formats for activity based models or regular transport models. Facilitate preliminary **Analysis** and **Validation** of changes.

This work is primarily intended for transport modellers, to make quick transport demand
scenarios. But it may also be useful for other activity based demand modelling such as for goods
supply or utility demand.

<!--- --8<-- [end:docs] -->
## Installation

To install PAM, we recommend using the [mamba](https://mamba.readthedocs.io/en/latest/index.html) package manager:

### As a user
<!--- --8<-- [start:docs-install-user] -->
``` shell
git clone git@github.com:arup-group/pam.git
cd pam
mamba create -n pam -c conda-forge -c city-modelling-lab --file requirements/base.txt
mamba activate pam
pip install --no-deps .
```
<!--- --8<-- [end:docs-install-user] -->
### As a developer
<!--- --8<-- [start:docs-install-dev] -->
``` shell
git clone git@github.com:arup-group/pam.git
cd pam
mamba create -n pam -c conda-forge -c city-modelling-lab --file requirements/base.txt --file requirements/dev.txt
mamba activate pam
pip install --no-deps -e .
```
<!--- --8<-- [end:docs-install-dev] -->
For more detailed instructions, see our [documentation](https://arup-group.github.io/pam/latest/installation/).

## Contributing

There are many ways to make both technical and non-technical contributions to PAM.
Before making contributions to the PAM source code, see our contribution guidelines and follow the [development install instructions](#as-a-developer).

If you are using `pip` to install PAM instead of the recommended `mamba`, you can install the optional test and documentation libraries using the `dev` option, i.e., `pip install -e '.[dev]'`

If you plan to make changes to the code then please make regular use of the following tools to verify the codebase while you work:

- `pre-commit`: run `pre-commit install` in your command line to load inbuilt checks that will run every time you commit your changes. 
The checks are: 1. check no large files have been staged, 2. lint python files for major errors, 3. format python files to conform with the [pep8 standard](https://peps.python.org/pep-0008/). 
You can also run these checks yourself at any time to ensure staged changes are clean by simple calling `pre-commit`.
- `pytest` - run the unit test suite, check test coverage, and test that the example notebooks successfully run.
- `pytest -p memray -m "high_mem" --no-cov` (not available on Windows) - after installing memray (`mamba install memray pytest-memray`), test that memory and time performance does not exceed benchmarks.

For more information, see our [documentation](https://arup-group.github.io/pam/latest/contributing/coding/).

## Building the documentation

If you are unable to access the online documentation, you can build the documentation locally.
First, [install a development environment of PAM](https://arup-group.github.io/pam/latest/contributing/coding/), then deploy the documentation using [mike](https://github.com/jimporter/mike):

```
mike deploy 0.2
mike serve
```

Then you can view the documentation in a browser at http://localhost:8000/.