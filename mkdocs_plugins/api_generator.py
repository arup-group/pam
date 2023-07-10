"""Plugin to add all source code files as individual API reference documents in the documentation.
Each source code file with have a separate page in the documentation, with pages nested in line with the soruce code directory nesting.
"""
import tempfile
import textwrap
from pathlib import Path
from typing import Union

import mkdocs
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files


class AddAPIPluginConfig(mkdocs.config.base.Config):
    """Enable the plugin configuration options."""

    # directory in which the source code is placed.
    package_dir = config_options.Type(str)

    # directory in the mkdocs structure to place the symbolic links to temporary markdown files.
    api_dir = config_options.Type(str, default="api")

    # List of files to skip generating an API page for.
    skip = config_options.Type(list, default=[])


class AddAPIPlugin(BasePlugin[AddAPIPluginConfig]):
    """Generate a Markdown file per source code python file which provides the hook for
    `mkdocstrings` to convert the file's docstrings to HTML API reference pages.
    """

    def __init__(self, *args, **kwargs):
        """Add instance attributes to the plugin."""
        super().__init__(*args, **kwargs)

        self._tmpdir = tempfile.TemporaryDirectory(prefix="mkdocs_api_file_generator_")
        """Temporary directory to store generated markdown files"""

        self._api_reference: dict[str, Union[list, dict[str, list]]] = {"top_level": []}
        """Dictionary to store navigation elements, which will be added to the mkdocs `nav`"""

    def on_files(self, files: Files, config: Config) -> Files:
        """`on_files` is an mkdocs event handler which can be used to add files to the docs directory that mkdocs sees when building the documentation.

        Args:
            files (Files): Initial set of files, as found in the `docs` directory.
            config (Config): Dictionary of the mkdocs configuration, containing all default config and the overrides procided in `mkdocs.yaml`.
        Keyword Args: Kept in case
        Returns:
            Files: Updated files list including pointers to the API markdown files which are stored in a temporary directory
        """
        for file in sorted(Path(self.config.package_dir).glob("**/[!_]*.py")):
            if file.as_posix() in self.config.skip:
                continue
            fileobj = self.py_to_md(file, config)
            files.append(fileobj)
        # Mkdocs navigation is composed of lists of dictionaries.
        # Lists nesting defines navigation nesting, dictionary keys are the page names, and values are the pointers to markdown files.
        api_reference_nav = {
            "Python API": [
                *self._api_reference.pop("top_level"),
                *[{k: v} for k, v in self._api_reference.items()],
            ]
        }
        nav_reference = [idx for idx in config["nav"] if set(idx.keys()) == {"Reference"}][0]
        nav_reference["Reference"].append(api_reference_nav)
        return files

    def py_to_md(self, filepath: Path, config: Config) -> File:
        """Create a markdown file for the API documentation for a given python file in the package source directory.
        Markdown files are stored in a temporary directory, which will be cleaned after mkdocs has finished building the docs.

        Args:
            filepath (Path): Path to python file in the package source directory.
            config (Config): mkdocs config dictionary.
        """
        module_parts = filepath.with_suffix("").parts
        module_name = ".".join(module_parts)
        # TODO: add plugin config options to enable custom mkdocstrings options to be applied for specific files
        template = textwrap.dedent(
            f"""
        ::: { module_name }
        """
        )

        api_file = Path(self.config.api_dir) / Path(*filepath.with_suffix(".md").parts[1:])
        api_full_filepath = Path(self._tmpdir.name) / api_file
        api_full_filepath.parent.mkdir(exist_ok=True, parents=True)
        api_full_filepath.write_text(template)

        nav_component = {module_name: api_file.as_posix()}
        if len(module_parts) > 2:  # i.e., in a nested directory
            parent_module = ".".join(module_parts[:2])
            if parent_module not in self._api_reference:
                self._api_reference[parent_module] = [nav_component]
            else:
                self._api_reference[parent_module].append(nav_component)
        else:
            self._api_reference["top_level"].append(nav_component)
        return File(
            path=api_file,
            src_dir=self._tmpdir.name,
            dest_dir=config["site_dir"],
            use_directory_urls=config["use_directory_urls"],
        )

    @mkdocs.plugins.event_priority(-100)
    def on_post_build(self, config: Config):
        """After mkdocs has finished building the docs, remove the temporary directory of markdown files.

        Args:
            config (Config): mkdocs config dictionary (unused).
        """
        self._tmpdir.cleanup()
