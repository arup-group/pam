import click
import logging
from pathlib import Path
from typing import Optional
import os
from rich.progress import track
from rich.console import Console
import geopandas as gp

from pam.operations.cropping import simplify_population
from pam.operations.combine import pop_combine
from pam.samplers import population as population_sampler
from pam import read, write
from pam.report.summary import pretty_print_summary, print_summary
from pam.report.stringify import stringify_plans
from pam.report.benchmarks import benchmarks as bms


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-3s %(message)s',
)
logger = logging.getLogger(__name__)


def common_options(func):
    func = click.option(
        '-d', '--debug', is_flag=True, help="Switch on debug verbosity."
    )(func)
    return func


def common_matsim_options(func):
    func = click.option(
        "--matsim_version", "-v",
        type=int, default=12,
        help="MATSim plan format, default 12."
    )(func)
    func = click.option(
        "--household_key",
        "-h",
        type=str,
        default=None,
        help="Household key, such as 'hid', default None."
    )(func)
    func = click.option(
        "--simplify_pt_trips",
        is_flag=True,
        default=False,
        help="Optionally simplify transit legs into single trip."
    )(func)
    func = click.option(
        "--autocomplete/--no_autocomplete",
        default=True,
        help="Optionally turn off autocomplete, not recommended."
    )(func)
    func = click.option(
        "--crop/--no_crop",
        default=False,
        help="Crop or don't crop plans to 24 hours, defaults to crop."
    )(func)
    func = click.option(
        "--leg_attributes/--no_leg_attributes",
        default=True,
        help="Optionally turn of reading of leg_attributes."
    )(func)
    func = click.option(
        "--leg_route/--no_leg_route",
        default=True,
        help="Optionally turn off reading of leg_route."
    )(func)
    func = click.option(
        "--keep_non_selected/--selected_only",
        default=False,
        help="Optionally keep (read and write) non selected plans."
    )(func)
    return func


def comment_option(func):
    func = click.option(
        "--comment", "-c", default="",
        help="A comment included in the output population."
    )(func)
    return func


@click.group()
def cli():
    """
    Population Activity Modeller (PAM) Command Line Tool
    """
    pass


@cli.group()
def report():
    """
    Various reporting for MATSim formatted plans.
    """
    pass


@report.command()
@common_options
@common_matsim_options
@click.argument(
    "path_population_input",
    type=click.Path(exists=True)
    )
@click.option(
    "--sample_size",
    "-s",
    type=float,
    default=1,
    help="Input sample size. Default 1. For example, use 0.1 to apply a 10% weighting to the input population."
    )
@click.option(
    "--attribute_key",
    "-k",
    help="Optional population attribute key to segment output, eg 'subpopulation'."
    )
@click.option(
    "--rich/--text",
    default=True,
    help="Formatted (for terminal) or regular text output (for .txt)."
    )
def summary(
    path_population_input: str,
    sample_size: float,
    matsim_version: int,
    attribute_key: str,
    household_key: str,
    simplify_pt_trips: bool,
    autocomplete : bool,
    crop: bool,
    leg_attributes: bool,
    leg_route: bool,
    keep_non_selected: bool,
    debug: bool,
    rich: bool,
    ):
    """
    Summarise a population.
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    # read
    logger.info(f"Loading plans from {path_population_input}.")
    logger.debug(f"Attribute key = {attribute_key}.")
    logger.debug(f"Sample size = {sample_size}.")
    logger.debug(f"MATSim version set to {matsim_version}.")
    logger.debug(f"'household_key' set to {household_key}.")
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    print(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")
    logger.debug(f"Keep non selected plans (recommended for warm starting) = {keep_non_selected}")

    with Console().status("[bold green]Loading population...", spinner='aesthetic') as _:
        population = read.read_matsim(
            path_population_input,
            household_key=household_key,
            weight=int(1/sample_size),
            version=matsim_version,
            simplify_pt_trips=simplify_pt_trips,
            autocomplete=autocomplete,
            crop=crop,
            leg_attributes=leg_attributes,
            leg_route=leg_route,
            keep_non_selected=keep_non_selected,
        )
    logger.info("Loading complete.")
    if rich:
        pretty_print_summary(population, attribute_key)
    else:
        print_summary(population, attribute_key)


@report.command()
@click.argument("population_input_path", type=click.Path(exists=True))
@click.argument("output_directory", type=click.Path(exists=False, writable=True))
@click.option(
    "--sample_size",
    "-s",
    type=float,
    default=1,
    help="Input sample size. Default 1. Required for downsampled populations. eg, use 0.1 for a 10% input population."
    )
@common_options
def benchmarks(
    population_input_path: str,
    output_directory: str,
    sample_size: float = 1.,
    matsim_version: int = 12,
    debug: bool = False,
    ):
    """
    Write batch of benchmarks to directory
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    # read
    logger.info(f"Loading plans from {population_input_path}.")
    logger.debug(f"Sample size = {sample_size}.")
    logger.debug(f"MATSim version set to {matsim_version}.")

    with Console().status("[bold green]Loading population...", spinner='aesthetic') as _:
        population = read.read_matsim(
            population_input_path,
            version=matsim_version,
            weight=int(1/sample_size),
        )
    logger.info("Loading complete, creating benchmarks...")

    # export
    if not os.path.exists(output_directory):
        logger.debug(f"Creating output directory: {output_directory}")
        os.makedirs(output_directory)

    console = Console()
    with console.status("[bold green]Building benchmarks...", spinner='aesthetic') as _:
        for name, bm in bms(population):
            path = os.path.join(output_directory, name)
            logger.debug(f"Writing benchmark to {path}.")
            if name.lower().endswith('.csv'):
                bm.to_csv(path, index=False)
            elif name.lower().endswith('.json'):
                bm.to_json(path, orient='records')
            else:
                raise UserWarning('Please specify a valid csv or json file path.')
            console.log(f"{name} written to disk.")
    logger.info("Done.")


@report.command()
@click.argument("path_population_input", type=click.Path(exists=True))
@click.option(
    "--colour/--bw", default=True,
    help="Choose a colour or grey-scale (bw) output, default 'colour'"
    )
@click.option(
    "--width", "-w", type=int, default=72,
    help="Target character width for plot, default 72"
    )
@click.option(
    "--simplify_pt_trips",
    is_flag=True,
    default=False,
    help="Optionally simplify transit legs into single trip."
    )
@click.option(
    "--crop/--no_crop",
    default=True,
    help="Crop or don't crop plans to 24 hours, defaults to crop."
    )
def stringify(
    path_population_input: str,
    colour: bool,
    width: int,
    simplify_pt_trips: bool,
    crop: bool,
    ):
    """
    ASCII plot activity plans to terminal.
    """
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Crop = {crop}")

    stringify_plans(
        path_population_input,
        colour,
        width
        )



@cli.command()
@common_options
@common_matsim_options
@comment_option
@click.argument(
    "path_population_input", type=click.Path(exists=True),
    )
@click.argument(
    "path_boundary", type=click.Path(exists=True),
    )
@click.argument(
    "dir_population_output", type=click.Path(exists=False, writable=True),
    )
@click.option(
    "--buffer", "-b", default=0,
    help="A buffer distance to (optionally) apply to the core area shapefile."
    )
def crop(
    path_population_input,
    path_boundary,
    dir_population_output,
    matsim_version,
    household_key,
    simplify_pt_trips: bool,
    autocomplete : bool,
    crop: bool,
    leg_attributes: bool,
    leg_route: bool,
    keep_non_selected: bool,
    comment,
    buffer,
    debug
    ):
    """
    Crop a population's plans outside a core area.
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting population cropping')
    logger.debug(f"Loading plans from {path_population_input}.")
    logger.debug(f"Loading boundary from {path_boundary}.")
    logger.debug(f"Buffer = {buffer}")
    logger.debug(f"Writing cropped plans to {dir_population_output}.")
    logger.debug(f"MATSim version set to {matsim_version}.")
    logger.debug(f"'household_key' set to {household_key}.")
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")
    logger.debug(f"Keep non selected plans (recommended for warm starting) = {keep_non_selected}")

    # core area geometry
    with Console().status("[bold green]Loading boundary...", spinner='aesthetic') as _:
        boundary = gp.read_file(path_boundary)
        boundary = boundary.dissolve().geometry[0]
    if buffer:
        with Console().status("[bold green]Buffering boundary...", spinner='aesthetic') as _:
            boundary = boundary.buffer(buffer)

    # crop population
    with Console().status("[bold green]Loading population...", spinner='aesthetic') as _:
        population = read.read_matsim(
            path_population_input,
            household_key=household_key,
            version=matsim_version,
            simplify_pt_trips=simplify_pt_trips,
            autocomplete=autocomplete,
            crop=crop,
            leg_attributes=leg_attributes,
            leg_route=leg_route,
            keep_non_selected=keep_non_selected,
        )

    with Console().status("[bold green]Applying simplification...", spinner='aesthetic') as _:
        simplify_population(population, boundary)
    logger.info('Population cropping complete')

    if not os.path.exists(dir_population_output):
        os.makedirs(dir_population_output)

    with Console().status("[bold green]Writing population...", spinner='aesthetic') as _:
        write.write_matsim(
            population,
            plans_path=os.path.join(dir_population_output, 'plans.xml'),
            comment=comment,
            keep_non_selected=keep_non_selected,
        )
    logger.info(f'Output saved at {dir_population_output}/plan.xml')


@cli.command()
@common_options
@common_matsim_options
@comment_option
@click.argument(
    "population_paths", type=click.Path(exists=True), nargs=-1
    )
@click.option(
    "--population_output", "-o", type=click.Path(exists=False, writable=True), default=os.getcwd()+"\combined_population.xml",
    help="Specify outpath for combined_population.xml, default is cwd"
    )
@click.option(
    "--force", "-f", is_flag=True,
    help="Forces overwrite of existing file."
    )
def combine(
    population_paths: str,
    population_output: str,
    matsim_version: int,
    household_key,
    simplify_pt_trips: bool,
    autocomplete : bool,
    crop: bool,
    leg_attributes: bool,
    leg_route: bool,
    keep_non_selected: bool,
    comment: str,
    force: bool,
    debug: bool
    ):
    """
    Combine multiple populations (e.g. household, freight.. etc).
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting population combiner')
    logger.debug(f"Loading plans from {population_paths}.")
    logger.debug(f"MATSim version set to {matsim_version}.")
    logger.debug(f"'household_key' set to {household_key}.")
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")
    logger.debug(f"Keep non selected plans (recommended for warm starting) = {keep_non_selected}")

    if not force and os.path.exists(population_output):
        if input(f"{population_output} exists, overwrite? [y/n]:") .lower() in ["y", "yes", "ok"]:
           pass
        else:
            raise UserWarning(f"Aborting to avoid overwrite of {population_output}")

    with Console().status("[bold green]Loading and combining populations...", spinner='aesthetic') as _:
        combined_population = pop_combine(
            inpaths=population_paths,
            matsim_version=matsim_version,
            household_key=household_key,
            simplify_pt_trips=simplify_pt_trips,
            autocomplete=autocomplete,
            crop=crop,
            leg_attributes=leg_attributes,
            leg_route=leg_route,
            keep_non_selected=keep_non_selected,
            )

    logger.debug(f"Writing combinined population to {population_output}.")

    with Console().status("[bold green]Writing population...", spinner='aesthetic') as _:
        write.write_matsim(
            population = combined_population,
            plans_path=population_output,
            comment=comment,
            keep_non_selected=keep_non_selected,
        )
    logger.info('Population combiner complete')
    logger.info(f'Output saved at {population_output}')


@cli.command()
@common_options
@common_matsim_options
@comment_option
@click.argument(
    "path_population_input", type=click.Path(exists=True),
    )
@click.argument(
    "dir_population_output", type=click.Path(exists=False, writable=True),
    )
@click.option(
    "--sample_size", "-s",
    help="The sample size, eg, use 0.1 to produce a 10% version of the input population."
    )
@click.option(
    "--household_key", "-h", type=str, default="hid",
    help="Household key, defaults to 'hid'."
    )
@click.option(
    "--seed", default=None,
    help="Random seed."
    )
def sample(
    path_population_input: str,
    dir_population_output: str,
    sample_size: str,
    matsim_version: int,
    household_key: str,
    simplify_pt_trips: bool,
    autocomplete : bool,
    crop: bool,
    leg_attributes: bool,
    leg_route: bool,
    keep_non_selected: bool,
    comment: str,
    seed: Optional[int],
    debug: bool,
    ):
    """
    Down- or up-sample a PAM population.
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting population sampling')
    logger.debug(f"Loading plans from {path_population_input}.")
    logger.debug(f"Sample size = {sample_size}.")
    logger.debug(f"Seed = {seed}")
    logger.debug(f"Writing cropped plans to {dir_population_output}.")
    logger.debug(f"MATSim version set to {matsim_version}.")
    logger.debug(f"'household_key' set to {household_key}.")
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")
    logger.debug(f"Keep non selected plans (recommended for warm starting) = {keep_non_selected}")

    # read
    with Console().status("[bold green]Loading population...", spinner='aesthetic') as _:
        population_input = read.read_matsim(
            path_population_input,
            household_key=household_key,
            weight=1,
            version=matsim_version,
            simplify_pt_trips=simplify_pt_trips,
            autocomplete=autocomplete,
            crop=crop,
            leg_attributes=leg_attributes,
            leg_route=leg_route,
            keep_non_selected=keep_non_selected,
        )
    logger.info(f'Initial population size (number of agents): {len(population_input)}')

    # sample
    sample_size = float(sample_size)
    population_output = population_sampler.sample(
        population=population_input,
        sample=sample_size,
        seed=seed,
        verbose=True
    )

    # export
    if not os.path.exists(dir_population_output):
        os.makedirs(dir_population_output)

    with Console().status("[bold green]Writing population...", spinner='aesthetic') as _:
        write.write_matsim(
            population_output,
            plans_path=os.path.join(dir_population_output, 'plans.xml'),
            comment=comment,
            keep_non_selected=keep_non_selected
        )

    logger.info('Population sampling complete')
    logger.info(f'Output population size (number of agents): {len(population_output)}')
    logger.info(f'Output saved at {dir_population_output}/plans.xml')
