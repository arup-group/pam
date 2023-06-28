
# Installation

It is easiest to install PAM using a [mamba](https://mamba.readthedocs.io/en/latest/index.html) environment, as follows:

1. Install mamba with the [Mambaforge] executable for your operating system.
2. Open the command line (or the "miniforge prompt" in Windows).
3. Download (a.k.a., clone) the PAM respository: `git clone git@github.com:arup-group/pam.git`
4. Create the PAM mamba environment: `mamba env create -f pam/environment.yml`
5. Activate the PAM mamba environment: `mamba activate pam`
6. Install the PAM package into the environment, in editible mode and ignoring dependencies (we have dealt with those when creating the mamba environment): `pip install --no-deps -e ./pam`

All together:

``` shell
git clone git@github.com:arup-group/pam.git
mamba env create -f pam/environment.yml
mamba activate pam
pip install --no-deps -e ./pam
```

We do not recommend trying to install PAM directly with pip (e.g. in a virtual environment) as you need to first install underlying native geospatial libraries, the method for which differs by operating system.
If you choose to install into a virtual environment, ensure you have `libgdal` and `libspatialindex` installed on your device before installing with pip. 

## Setting up a development environment

For installation instructions specific to developing the PAM codebase, see [here](get_involved.md#setting-up-a-development-environment)
