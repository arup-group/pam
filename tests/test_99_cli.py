import os

import pytest
from click.testing import CliRunner
from pam import read
from pam.cli import cli


@pytest.fixture
def path_test_plan():
    return os.path.join("tests", "test_data", "test_matsim_plansv12.xml")


@pytest.fixture
def path_test_plans_A():
    return os.path.join("tests", "test_data", "test_matsim_population_A.xml")


@pytest.fixture
def path_test_plans_B():
    return os.path.join("tests", "test_data", "test_matsim_population_B.xml")


@pytest.fixture
def path_boundary():
    return os.path.join("tests", "test_data", "test_geometry.geojson")


@pytest.fixture
def path_output_dir():
    return os.path.join("tests", "test_data", "output", "cropped")


def test_test_cli_summary(path_test_plan):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "report",
            "summary",
            path_test_plan,
            "-k",
            "subpopulation",
            "-s",
            "0.1",
            "-d",
            "--no_crop",
            "-h",
            "hid",
            "--simplify_pt_trips",
        ],
    )
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0
    result = runner.invoke(
        cli,
        [
            "report",
            "summary",
            path_test_plan,
            "-k",
            "subpopulation",
            "-s",
            "0.1",
            "-d",
            "--text",
            "--no_crop",
            "-h",
            "hid",
        ],
    )
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0


def test_benchmarking(path_test_plan, tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "benchmarks", str(path_test_plan), str(tmp_path)])
    assert result.exit_code == 0
    assert os.path.exists(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "mode_counts.csv"))


def test_stringify(path_test_plan):
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "stringify", path_test_plan, "-w", "144", "--bw"])
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0


def test_cli_cropping(path_test_plan, path_boundary, tmp_path):
    path_output_dir = str(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["crop", path_test_plan, path_boundary, path_output_dir])
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(path_output_dir, "plans.xml"))


def test_combine(path_test_plans_A, path_test_plans_B, tmp_path):
    path_output_dir = str(os.path.join(tmp_path, "plans.xml"))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["combine", path_test_plans_A, path_test_plans_B, "-o", path_output_dir]
    )
    assert result.exit_code == 0
    assert os.path.exists(path_output_dir)


@pytest.mark.parametrize("sample_percentage", ["1", "2"])
def test_cli_sample(path_test_plan, tmp_path, sample_percentage):
    """Double the population of 5 agents."""
    path_output_dir = str(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["sample", path_test_plan, path_output_dir, "-s", sample_percentage]
    )
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(path_output_dir, "plans.xml"))

    population_input = read.read_matsim(path_test_plan, household_key="hid", version=12)

    population = read.read_matsim(
        os.path.join(path_output_dir, "plans.xml"), household_key="hid", version=12
    )
    assert len(population) == (len(population_input) * float(sample_percentage))


def test_cli_wipe_all_links(path_test_plan, tmp_path):
    population_input = read.read_matsim(path_test_plan, household_key="hid", version=12)
    path_output_dir = str(tmp_path)
    path_output = os.path.join(path_output_dir, "test_out.xml", "--keep_non_selected")
    runner = CliRunner()
    result = runner.invoke(cli, ["wipe-all-links", path_test_plan, path_output])
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0
    assert os.path.exists(path_output)

    population = read.read_matsim(path_output, household_key="hid", version=12, leg_route=True)
    assert len(population) == len(population_input)
    for _, _, person in population.people():
        for leg in person.legs:
            assert not leg.route.exists
        for act in person.activities:
            assert act.location.link is None


def test_cli_link_wipe_selected_only(path_test_plan, tmp_path):
    population_input = read.read_matsim(path_test_plan, household_key="hid", version=12)
    path_output_dir = str(tmp_path)
    path_output = os.path.join(path_output_dir, "test_out.xml")
    runner = CliRunner()
    result = runner.invoke(
        cli, ["wipe-links", path_test_plan, path_output, "3-4", "--keep_non_selected"]
    )
    if result.exit_code != 0:
        print(result.output)
    assert result.exit_code == 0
    assert os.path.exists(path_output)

    population = read.read_matsim(
        path_output, household_key="hid", version=12, leg_route=True, keep_non_selected=True
    )
    assert len(population) == len(population_input)
    for _, _, person in population.people():
        for leg in person.legs:
            assert "3-4" not in leg.route.network_route
        for act in person.acts:
            assert act.location.link != "3-4"
