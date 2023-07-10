import os
import textwrap
from pathlib import Path

import pytest
from mkdocs.structure.files import File

from mkdocs_plugins import api_generator


@pytest.fixture
def temp_src_dir(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    file_1 = src_dir / "file_1.py"
    file_1_ignore = src_dir / "file_1_ignore.py"
    file_1_autoignore = src_dir / "_private_file.py"

    temp_sub_dir = src_dir / "subdir"
    temp_sub_dir.mkdir()
    file_2 = temp_sub_dir / "file_2.py"
    file_3 = temp_sub_dir / "file_3.py"
    file_2_ignore = temp_sub_dir / "file_2_ignore.py"

    for file in [file_1, file_2, file_3, file_1_ignore, file_2_ignore, file_1_autoignore]:
        file.write_text(
            textwrap.dedent(
                """
            def foo():
                return 1
            """
            )
        )
    return src_dir


@pytest.fixture(scope="module")
def curdir():
    return os.getcwd()


@pytest.fixture(scope="function")
def api_plugin():
    plugin = api_generator.AddAPIPlugin()
    plugin.load_config(
        {"package_dir": "src", "skip": ["src/file_1_ignore.py", "src/subdir/file_2_ignore.py"]}
    )
    return plugin


@pytest.fixture(scope="function")
def base_config(tmp_path: Path):
    site_dir = tmp_path / "site_dir"
    site_dir.mkdir()
    return {"nav": [{"Reference": []}], "site_dir": site_dir, "use_directory_urls": True}


@pytest.mark.parametrize(
    ["input_path", "expected_api_dict"],
    [
        ("src/foo.py", {"top_level": [{"src.foo": "api/foo.md"}]}),
        ("src/foo/bar.py", {"top_level": [], "src.foo": [{"src.foo.bar": "api/foo/bar.md"}]}),
        (
            "src/foo/bar/baz.py",
            {"top_level": [], "src.foo": [{"src.foo.bar.baz": "api/foo/bar/baz.md"}]},
        ),
    ],
)
def test_api_reference_populated(api_plugin, base_config, input_path, expected_api_dict):
    api_plugin.py_to_md(Path(input_path), base_config)

    assert api_plugin._api_reference == expected_api_dict


@pytest.mark.parametrize(
    ["input_path", "output_path", "module_name"],
    [("src/foo.py", "api/foo.md", "src.foo"), ("src/foo/bar.py", "api/foo/bar.md", "src.foo.bar")],
)
def test_generate_md(api_plugin, base_config, input_path, output_path, module_name):
    api_plugin.py_to_md(Path(input_path), base_config)

    assert Path(api_plugin._tmpdir.name, output_path).read_text() == textwrap.dedent(
        f"""
    ::: {module_name}
    """
    )


def test_generate_md_from_py(curdir, temp_src_dir, api_plugin, base_config):
    os.chdir(temp_src_dir / "..")

    files = api_plugin.on_files([], base_config)

    assert all(isinstance(i, File) for i in files)
    assert {file.name for file in files} == {"file_1", "file_2", "file_3"}

    assert base_config["nav"] == [
        {
            "Reference": [
                {
                    "Python API": [
                        {"src.file_1": "api/file_1.md"},
                        {
                            "src.subdir": [
                                {"src.subdir.file_2": "api/subdir/file_2.md"},
                                {"src.subdir.file_3": "api/subdir/file_3.md"},
                            ]
                        },
                    ]
                }
            ]
        }
    ]

    os.chdir(curdir)


def test_clear_tmpdir(api_plugin, base_config):
    assert Path(api_plugin._tmpdir.name).exists()

    api_plugin.on_post_build(base_config)

    assert not Path(api_plugin._tmpdir.name).exists()
