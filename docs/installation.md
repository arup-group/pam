
# Installation

## Setting up a user environment

As a PAM user, it is easiest to install PAM using the [mamba](https://mamba.readthedocs.io/en/latest/index.html) package manager, as follows:

1. Install mamba with the [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) executable for your operating system.
2. Open the command line (or the "miniforge prompt" in Windows).
3. Download (a.k.a., clone) the PAM repository: `git clone git@github.com:arup-group/pam.git`
4. Change into the `pam` directory: `cd pam`
5. Create the PAM mamba environment: `mamba create -n pam -c conda-forge -c city-modelling-lab --file requirements/base.txt`
6. Activate the PAM mamba environment: `mamba activate pam`
7. Install the PAM package into the environment, ignoring dependencies (we have dealt with those when creating the mamba environment): `pip install --no-deps .`

All together:

--8<-- "README.md:docs-install-user"

We do not recommend trying to install PAM directly with pip (e.g. in a virtual environment) as you need to first install underlying native geospatial libraries, the method for which differs by operating system.
If you choose to install into a virtual environment, ensure you have `libgdal` and `libspatialindex` installed on your device before installing with pip. 

### Running the example notebooks
If you have followed the non-developer installation instructions above, you will need to install `jupyter` into your `pam` environment to run the [example notebooks](https://github.com/arup-group/pam/tree/main/examples):

``` shell
mamba install -n pam jupyter
```

With Jupyter installed, it's easiest to then add the environment as a jupyter kernel: 

``` shell
mamba activate pam
ipython kernel install --user --name=pam
jupyter notebook
```

### Choosing a different environment name
If you would like to use a different name to `pam` for your mamba environment, the installation becomes (where `[my-env-name]` is your preferred name for the environment):

``` shell
mamba create -n [my-env-name] -c conda-forge -c city-modelling-lab --file requirements/base.txt
mamba activate [my-env-name]
ipython kernel install --user --name=[my-env-name]
```

## Setting up a development environment

The install instructions are slightly different to create a development environment compared to a user environment:

--8<-- "README.md:docs-install-dev"

For more detailed installation instructions specific to developing the PAM codebase, see our [development documentation][setting-up-a-development-environment].
