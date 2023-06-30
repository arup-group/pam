# Coding contributions

To find beginner-friendly existing bugs and feature requests you may like to start out with, take a look at our [good first issues](https://github.com/arup-group/pam/contribute).

We need help to **go faster** as we would like to deal with populations in the tens of millions.
This means we would like help with profiling and implementing parallel compute, in particular.

## Setting up a development environment

If you have followed the recommended installation instructions, all libraries required for development and quality assurance will already be installed.
If installing directly with pip, you can install these libraries using the `dev` option, i.e., `pip install -e ./pam[dev]`
Either way, you should add your environment as a jupyter kernel, so the example notebooks can run in the tests: `ipython kernel install --user --name=pam`

If you plan to make changes to the code then please make regular use of the following tools to verify the codebase while you work:

- `pre-commit`: run `pre-commit install` in your command line to load inbuilt checks that will run every time you commit your changes.
The checks are: 1. check no large files have been staged, 2. lint python files for major errors, 3. format python files to conform with the [PEP8 standard](https://peps.python.org/pep-0008/).
You can also run these checks yourself at any time to ensure staged changes are clean by calling `pre-commit`.
- `pytest` - run the unit test suite, check test coverage, and test that the example notebooks successfully run.

!!! note

    If you have [chosen a different environment name][choosing-a-different-environment-name] to the default `pam`, you will need to add this as a pytest argument: `pytest --nbmake-kernel=[my-env-name]`

### Rapid-fire testing
The following options allow you to strip down the test suite to the bare essentials:

1. The test suite includes unit tests and integration tests (in the form of jupyter notebooks found in the `examples` directory). 
The integration tests can be slow, so if you want to avoid them during development, you should run `pytest tests/`.
2. You can avoid generating coverage reports, by adding the `--no-cov` argument: `pytest --no-cov`.
3. By default, the tests run with up to two parallel threads, to increase this to e.g. 4 threads: `pytest -n4`.

All together:

``` shell
pytest tests/ --no-cov -n4
```

!!! note

    You cannot debug failing tests and have your tests run in parallel, you will need to set `-n0` if using the `--pdb` flag

### Memory profiling
PAM can be memory intensive; we like to ensure that any development to the core code does not exacerbate this.
If you are running on a UNIX device (i.e., **not** on Windows), you can test whether any changes you have made adversely impact memory and time performance as follows:

1. Install [memray](https://bloomberg.github.io/memray/index.html) in your `pam` mamba environment: `mamba install memray pytest-memray`.
2. Run the memory profiling integration test: `pytest -p memray -m "high_mem" --no-cov`. 
3. Optionally, to visualise the memory allocation, run `pytest -p memray -m "high_mem" --no-cov --memray-bin-path=[my_path] --memray-bin-prefix=[my_prefix]` - where you must define `[my_path]` and `[my_prefix]` - followed by `memray flamegraph [my_path]/[my_prefix]-tests-test_100_memory_profiling.py-test_activity_loader.bin`.
You will then find the HTML report at `[my_path]/memray-flamegraph-[my_prefix]-tests-test_100_memory_profiling.py-test_activity_loader.html`.

All together:

``` shell
mamba install memray pytest-memray
pytest -p memray -m "high_mem" --no-cov --memray-bin-path=[my_path] --memray-bin-prefix=[my_prefix]
memray flamegraph [my_path]/[my_prefix]-tests-test_100_memory_profiling.py-test_activity_loader.bin
```

For more information on using memray, refer to their [documentation](https://bloomberg.github.io/memray/index.html).

## Submitting changes

--8<-- "CONTRIBUTING.md:docs"