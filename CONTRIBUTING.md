# Contributing guidelines

We're really glad you're reading this, because we need volunteer developers to help maintain this project.

Some of the resources to look at if you're interested in contributing:

* Look at open issues tagged with ["help wanted"](https://github.com/arup-group/pam/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) and ["good first issue"](https://github.com/arup-group/pam/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
* Look at the [contributing guide in our documentation](https://arup-group.github.io/pam/contributing)

## Licensing

By contributing to PAM, i.e. through opening a pull request, you represent that your contributions are your own original work and that you have the right to license them, and you agree that your contributions are licensed under the MIT license.

## Reporting bugs and requesting features 

You can open an issue on GitHub to report bugs or request new PAM features.
Follow these links to submit your issue:

- [Report bugs or other problems while running PAM](https://github.com/arup-group/pam/issues/new?template=BUG-REPORT.yml). 
If reporting an error, please include a full traceback in your issue.

- [Request features that PAM does not already include](https://github.com/arup-group/pam/issues/new?template=FEATURE-REQUEST.yml).


- [Report missing or inconsistent information in our documentation](https://github.com/arup-group/pam/issues/new?template=DOCS.yml).

- [Any other issue](https://github.com/arup-group/pam/issues/new).

## Submitting changes

Look at the [development guide in our documentation](https://arup-group.github.io/pam/contributing/coding) for information on how to get set up for development.

<!--- the "--8<--" html comments define what part of this file to add to the index page of the documentation -->
<!--- --8<-- [start:docs] -->

To contribute changes:

1. Fork the project on GitHub.
2. Create a feature branch to work on in your fork (`git checkout -b new-fix-or-feature`).
3. Test your changes using `pytest`.
4. Commit your changes to the feature branch (you should have `pre-commit` installed to ensure your code is correctly formatted when you commit changes).
5. Push the branch to GitHub (`git push origin new-fix-or-feature`).
6. On GitHub, create a new [pull request](https://github.com/arup-group/pam/pull/new/main) from the feature branch.

### Pull requests

Before submitting a pull request, check whether you have:

* Added your changes to `CHANGELOG.md`.
* Added or updated documentation for your changes.
* Added tests if you implemented new functionality.

When opening a pull request, please provide a clear summary of your changes!

### Commit messages

Please try to write clear commit messages. One-line messages are fine for small changes, but bigger changes should look like this:

    A brief summary of the commit (max 50 characters)

    A paragraph or bullet-point list describing what changed and its impact,
    covering as many lines as needed.

### Code conventions

Start reading our code and you'll get the hang of it.

We mostly follow the official [Style Guide for Python Code (PEP8)](https://www.python.org/dev/peps/pep-0008/).

We have chosen to use the uncompromising code formatter [`black`](https://github.com/psf/black/) and the linter [`ruff`](https://beta.ruff.rs/docs/).  
When run from the root directory of this repo, `pyproject.toml` should ensure that formatting and linting fixes are in line with our custom preferences (e.g., 100 character maximum line length).  
The philosophy behind using `black` is to have uniform style throughout the project dictated by code.  
Since `black` is designed to minimise diffs, and make patches more human readable, this also makes code reviews more efficient.  
To make this a smooth experience, you should run `pre-commit install` after setting up your development environment, so that `black` makes all the necessary fixes to your code each time you commit, and so that `ruff` will highlight any errors in your code. 
If you prefer, you can also set up your IDE to run these two tools whenever you save your files, and to have `ruff` highlight erroneous code directly as you type.
Take a look at their documentation for more information on configuring this.

We require all new contributions to have docstrings for all modules, classes and methods.
When adding docstrings, we request you use the [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

## Release checklist

### Pre-release

- [ ] Make sure all unit and integration tests pass (`pytest` and `pytest -p memray -m "high_mem" --no-cov` if you are able to use memray - see [memory-profiling][] for more info).
- [ ] Re-run tutorial Jupyter notebooks (`pytest examples/ --overwrite`).
- [ ] Make sure documentation builds without errors (`mike deploy [version]`, where `[version]` is the current minor release of the form `X.Y`).
- [ ] Make sure the [changelog][changelog] is up-to-date, especially that new features and backward incompatible changes are clearly marked.
- [ ] Ensure all requirements are up to date and that the files in the `requirements` directory are in sync with the `environment.yml` file.

### Create release

- [ ] Bump the version number in `setup.py`
- [ ] Update the [changelog][changelog] with final version number of the form `vX.Y.Z`, release date, and github `compare` link (at the bottom of the page).
- [ ] Commit with message `Release vX.Y.Z`, then add a `vX.Y.Z` tag, push both to GitHub
- [ ] Create a release through the GitHub web interface, using the same tag, titling it `Release vX.Y.Z` and include all the changelog elements that are *not* flagged as **internal**.

### Post-release

- [ ] Update the changelog, adding a new `[Unreleased]` heading, and update `setup.py` to the next version appended with `-dev`, in preparation for the next main commit.
- [ ] If bumping the major or minor version (`X`/`Y` in `X.Y.Z`), update the documentation version in the `build_pipeline` GitHub action (e.g., `mike deploy 0.2` -> `mike deploy 0.3`) and push an update to the pointer for the `latest` documentation from your own device: `mike deploy --push --update-aliases X.Y latest`.


<!--- --8<-- [end:docs] -->

## Attribution

The layout and content of this document is partially based on the [Calliope project's contribution guidelines](https://github.com/calliope-project/calliope/blob/main/CONTRIBUTING.md).
