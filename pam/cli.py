import click
import logging
from pathlib import Path


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
def crop(path_population_input, path_boundary, dir_population_output,
         matsim_version, comment):
    """
    Crop a population's plans outside a core area.
    :param path_population_input: Path to a MATSim population (xml)
    :param path_boundary: Path to the core area geojson file
    :param dir_population_output: Path to the output (cropped) MATSim population 
    :param matsim_version: MATSim version
    :param comment: A short comment included in the output population

    """
    from pam.cropping import crop_xml
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-3s %(message)s',
        datefmt='%m-%d %H:%M'
    )
    logger = logging.getLogger(__name__)
    logger.info('Starting population cropping')
    crop_xml(
        path_population_input = path_population_input,
        path_boundary = path_boundary,
        dir_population_output = dir_population_output,
        version = matsim_version,
        comment = comment
    )
    logger.info('Population cropping complete')
    logger.info(f'Output saved at {dir_population_output}/plan.xml')
