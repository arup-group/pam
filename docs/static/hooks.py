from pathlib import Path

import mkdocs.plugins
from mkdocs.structure.files import File


# Bump priority to ensure files are moved before jupyter notebook conversion takes place
@mkdocs.plugins.event_priority(50)
def on_files(files: list, config: dict, **kwargs):
    """Link top-level files to mkdocs files."""
    for file in Path("./examples").glob("*.ipynb"):
        files.append(_new_file(file, config))
    for file in Path("./resources").glob("**/*.*"):
        files.append(_new_file(file, config))
    files.append(_new_file("./CHANGELOG.md", config))
    return files


def _new_file(path: Path, config: str) -> File:
    return File(
        path=path,
        src_dir=".",
        dest_dir=config["site_dir"],
        use_directory_urls=config["use_directory_urls"],
    )
