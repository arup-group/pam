import tempfile
from pathlib import Path

import mkdocs.plugins
from mkdocs.structure.files import File

TEMPDIR = tempfile.TemporaryDirectory()
API_FILES_TO_IGNORE = ["cli.py", "variables.py"]


# Bump priority to ensure files are moved before jupyter notebook conversion takes place
@mkdocs.plugins.event_priority(50)
def on_files(files: list, config: dict, **kwargs):
    """Link (1) top-level files to mkdocs files and (2) generate the python API documentation."""
    for file in sorted(Path("./examples").glob("*.ipynb")):
        files.append(_new_file(file, config))
        nav_reference = [idx for idx in config["nav"] if set(idx.keys()) == {"Examples"}][0]
        nav_reference["Examples"].append(file.as_posix())
    for file in Path("./resources").glob("**/*.*"):
        files.append(_new_file(file, config))
    files.append(_new_file("./CHANGELOG.md", config))

    api_nav = _api_gen(files, config)
    _update_nav(api_nav, config)

    return files


def _new_file(path: Path, config: dict, src_dir: str = ".") -> File:
    """Link a file out in the wilderness to a filename in the documentation directory hierarchy.

    Args:
        path (Path):
            Path (relative to "src_dir") to file that you want to bring into the documentation directory.
            In the documentation directory, this same path with apply (e.g., `[src_dir]/path/to/file.md` will become `[docs_dir]/path/to/file.md`)
        config (dict): mkdocs config dictionary.
        src_dir (str, optional):
            Path in which to find the file you want to bring into the docs directory. Defaults to ".".

    Returns:
        File: mkdocs object that links your file to the docs directory, ready to be added to the mkdocs file list.
    """
    return File(
        path=path,
        src_dir=src_dir,
        dest_dir=config["site_dir"],
        use_directory_urls=config["use_directory_urls"],
    )


def _api_gen(files: list, config: dict) -> dict:
    """Project Python API generator

    Args:
        files (list): mkdocs file list.
        config (dict): mkdocs config dictionary.

    Returns:
        dict: Python API navigation tree, to add into the mkdocs `nav` tree.
    """
    source_dir = Path(config["watch"][0])
    source_file = source_dir.parts[-1]
    api_nav: dict = {"top_level": []}
    for filepath in sorted(source_dir.rglob("[!_]*.py")):
        rel_filepath = filepath.relative_to(source_dir)
        if rel_filepath.as_posix() in API_FILES_TO_IGNORE:
            continue
        file = _py_to_md(source_file / rel_filepath, api_nav, config)
        files.append(file)
    return api_nav


def _py_to_md(filepath: Path, api_nav: dict, config: dict) -> File:
    """Create a markdown file for the API documentation for a given python file in the package source directory.

    Markdown files are stored in a temporary directory, which will be cleaned after mkdocs has finished building the docs.

    Args:
        filepath (Path): Path to python file relative to the package source code directory.
        api_nav (dict): Nested dictionary to fill with mkdocs navigation entries.
        config (Config): mkdocs config dictionary.
    Returns:
        File: mkdocs object that links the temp file to the docs directory, ready to be added to the mkdocs file list.
    """
    module_parts = filepath.with_suffix("").parts

    module_name = ".".join(module_parts)

    api_file = "reference" / filepath.with_suffix(".md")
    api_full_filepath = Path(TEMPDIR.name) / api_file
    api_full_filepath.parent.mkdir(exist_ok=True, parents=True)
    api_full_filepath.write_text(f"::: {module_name}")

    nav_component = {module_name: api_file.as_posix()}
    if len(module_parts) > 2:  # i.e., in a nested directory
        parent_module = ".".join(module_parts[:2])
        if parent_module not in api_nav:
            api_nav[parent_module] = [nav_component]
        else:
            api_nav[parent_module].append(nav_component)
    else:
        api_nav["top_level"].append(nav_component)
    return _new_file(api_file, config, TEMPDIR.name)


def _update_nav(api_nav: dict, config: dict) -> None:
    """Update mkdocs navigation tree with the Python API sub-tree.

    Mkdocs navigation is composed of lists of dictionaries.
    Lists nesting defines navigation nesting, dictionary keys are the page names, and values are the pointers to markdown files.

    Args:
        api_nav (dict): Python API navigation tree.
        config (dict): mkdocs config dictionary (in which `nav` can be found).
    """

    api_reference_nav = {
        "Python API": [*api_nav.pop("top_level"), *[{k: v} for k, v in api_nav.items()]]
    }
    nav_reference = [idx for idx in config["nav"] if set(idx.keys()) == {"Reference"}][0]
    nav_reference["Reference"].append(api_reference_nav)


@mkdocs.plugins.event_priority(-100)
def on_post_build(**kwargs):
    """After mkdocs has finished building the docs, remove the temporary directory of markdown files.

    Args:
        config (Config): mkdocs config dictionary (unused).
    """
    TEMPDIR.cleanup()
