
# Installation

It is easiest to install PAM using a [mamba](https://mamba.readthedocs.io/en/latest/index.html) environment, as follows:

1. Install [Mambaforge](https://mamba.readthedocs.io/en/latest/installation.html).
2. Create a conda/mamba environment and install PAM into it:

``` shell
mamba create -n pam -c city-modelling-lab pam
mamba activate pam
```

We do not recommend trying to install PAM directly with pip (e.g. in a virtual environment) as you need to first install underlying native geospatial libraries, the method for which differs by operating system.
If you choose to install into a virtual environment, ensure you have `libgdal` and `libspatialindex` installed on your device before installing with pip. 

## Running the example notebooks
If you would like to run the [example notebooks](https://github.com/arup-group/pam/tree/main/examples), it's easiest to add the environment as a jupyter kernel: 

``` shell
mamba activate pam
ipython kernel install --user --name=pam
jupyter notebook
```

## Choosing a different environment name
If you would like to use a different name to `pam` for your mamba environment, the installation becomes (where `[my-env-name]` is your preferred name for the environment):

``` shell
mamba create -n pam -c city-modelling-lab [my-env-name]
mamba activate [my-env-name]
ipython kernel install --user --name=[my-env-name]
```

## Setting up a development environment

For installation instructions specific to developing the PAM codebase, see our [development documentation][setting-up-a-development-environment].
