import click
import logging
from pathlib import Path
from typing import Optional
import os

from pam.operations.combine import pop_combine
from pam.operations.cropping import crop_xml
from pam.samplers import population as population_sampler
from pam import read, write
from pam.report.summary import pretty_print_summary, print_summary
from pam.report.stringify import stringify_plans


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
        default="hid",
        help="Household key, default 'hid'."
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
    print(f"Simplif PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")

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
    )
    logger.info("Loading complete.")
    if rich:
        pretty_print_summary(population, attribute_key)
    else:
        print_summary(population, attribute_key)


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

    crop_xml(
        path_population_input=path_population_input,
        path_boundary=path_boundary,
        dir_population_output=dir_population_output,
        version=matsim_version,
        household_key=household_key,
        simplify_pt_trips=simplify_pt_trips,
        autocomplete=autocomplete,
        crop=crop,
        leg_attributes=leg_attributes,
        leg_route=leg_route,
        comment=comment,
        buffer=buffer
    )
    logger.info('Population cropping complete')
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

def combine(
    population_paths: str,
    population_output: str,
    matsim_version: int,
    simplify_pt_trips: bool,
    autocomplete : bool,
    crop: bool,
    leg_attributes: bool,
    leg_route: bool,
    comment: str,
    debug
    ):
    """
    Combine multiple populations (e.g. household, freight.. etc).
    """
    if os.path.exists(population_output) == True:
        if input(f"{population_output} exists, overwrite? [y/n]:") .lower() in ["y", "yes", "ok"]:
           pass
        else:
            raise UserWarning(f"Aborting to avoid overwrite of {population_output}")

    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting population combiner')
    logger.debug(f"Loading plans from {population_paths}.")
    logger.debug(f"MATSim version set to {matsim_version}.")
    logger.debug(f"Simplify PT trips = {simplify_pt_trips}")
    logger.debug(f"Autocomplete MATSim plans (recommended) = {autocomplete}")
    logger.debug(f"Crop = {crop}")
    logger.debug(f"Leg attributes (required for warm starting) = {leg_attributes}")
    logger.debug(f"Leg route (required for warm starting) = {leg_route}")

    combined_population = pop_combine(
        inpaths=population_paths,
        matsim_version=matsim_version,
        simplify_pt_trips=simplify_pt_trips,
        autocomplete=autocomplete,
        crop=crop,
        leg_attributes=leg_attributes,
        leg_route=leg_route,
        )

    logger.debug(f"Writing combinined population to {population_output}.")

    write.write_matsim(
        population = combined_population,
        version=matsim_version,
        plans_path=population_output,
        comment=comment
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

    # read
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

    write.write_matsim(
        population_output,
        plans_path=os.path.join(dir_population_output, 'plans.xml'),
        attributes_path=os.path.join(dir_population_output, 'attributes.xml'),
        version=matsim_version,
        comment=comment
    )

    logger.info('Population sampling complete')
    logger.info(f'Output population size (number of agents): {len(population_output)}')
    logger.info(f'Output saved at {dir_population_output}/plans.xml')
