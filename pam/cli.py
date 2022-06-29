import click
import logging
from pathlib import Path
from pam.cropping import crop_xml
from pam.samplers import population as population_sampler
from pam import read, write
from typing import Optional
import os


@click.group()
def cli():
    """
    Population Activity Modeller (PAM) Command Line Tool
    """
    pass


@cli.command()
@click.argument("path_population_input", type=click.Path(exists=True))
@click.argument("path_boundary", type=click.Path(exists=True))
@click.argument("dir_population_output", type=click.Path(exists=False, writable=True))
@click.option("--matsim_version", "-v", default=12)
@click.option("--comment", "-c", default="cropped population")
@click.option("--buffer", "-b", default=0)
def crop(path_population_input, path_boundary, dir_population_output,
         matsim_version, comment, buffer):
    """
    Crop a population's plans outside a core area.

    :param path_population_input: Path to a MATSim population (xml)
    :param path_boundary: Path to the core area geojson file
    :param dir_population_output: Path to the output (cropped) MATSim population 
    :param matsim_version: MATSim version
    :param comment: A short comment included in the output population
    :param buffer: A buffer distance to (optionally) apply to the core area shapefile

    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-3s %(message)s',
        datefmt='%m-%d %H:%M'
    )
    logger = logging.getLogger(__name__)
    logger.info('Starting population cropping')
    crop_xml(
        path_population_input=path_population_input,
        path_boundary=path_boundary,
        dir_population_output=dir_population_output,
        version=matsim_version,
        comment=comment,
        buffer=buffer
    )
    logger.info('Population cropping complete')
    logger.info(f'Output saved at {dir_population_output}/plan.xml')


@cli.command()
@click.argument("path_population_input", type=click.Path(exists=True))
@click.argument("dir_population_output", type=click.Path(exists=False, writable=True))
@click.option("--sample_percentage", "-s")
@click.option("--matsim_version", "-v", default=12)
@click.option("--comment", "-c", default="cropped population")
@click.option("--seed", default=None)
def sample(path_population_input: str, dir_population_output: str, sample_percentage: str,
           matsim_version: int, comment: str, seed: Optional[int]):
    """
    Down- or up-sample a PAM population.

    :param path_population_input: Path to a MATSim population (xml)
    :param dir_population_output: Path to the output (cropped) MATSim population 
    :param sample_percentage: The sample percentage (as a ratio to the input population size).
        For example, use 0.1 to produce a 10% version of the input population
    :param matsim_version: MATSim version
    :param comment: A short comment included in the output population
    :param seed: A random seed.

    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-3s %(message)s',
        datefmt='%m-%d %H:%M'
    )
    logger = logging.getLogger(__name__)
    logger.info('Starting population sampling')

    # read
    population_input = read.read_matsim(
        path_population_input,
        household_key="hid",
        weight=1,
        version=matsim_version
    )
    print(population_input)
    logger.info(f'Initial population size (number of agents): {len(population_input)}')

    # sample
    sample_percentage = float(sample_percentage)
    population_output = population_sampler.sample(
        population=population_input,
        sample=sample_percentage,
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
