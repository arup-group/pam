from mkdocs.structure.files import File
from pathlib import Path


def on_files(files, config, **kwargs):
    """Link top-level files to mkdocs files."""
    for file in Path("./examples").glob("*.ipynb"):
        files.append(_new_file(file, config))

    return files


def _new_file(path, config):
    return File(
        path=path,
        src_dir=".",
        dest_dir=config["site_dir"],
        use_directory_urls=config["use_directory_urls"],
    )
