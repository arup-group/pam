from click.testing import CliRunner
import click
import pytest
from pam.cli import crop
import os


@pytest.fixture
def path_test_plan():
    return os.path.join('tests', 'test_data', 'test_matsim_plansv12.xml')


@pytest.fixture
def path_boundary():
    return os.path.join('tests', 'test_data', 'test_geometry.geojson')


@pytest.fixture
def path_output_dir():
    return os.path.join('tests', 'test_data', 'output', 'cropped')


def test_cli_cropping(path_test_plan, path_boundary, tmp_path):
    """ Plan cropping CLI """
    path_output_dir = str(tmp_path)
    runner = CliRunner()
    result = runner.invoke(crop, [path_test_plan,
                           path_boundary, path_output_dir])
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(path_output_dir, 'plans.xml'))
