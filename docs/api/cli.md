# CLI Reference

This page provides documentation for our command line tools.

## Examples

* to get a summary or a MATSim plans file: `pam report summary tests/test_data/test_matsim_plansv12.xml`.
* plan cropping: `pam crop <path_population_xml> <path_core_area_geojson> <path_output_directory>`.
* down/up-sampling an xml population: `pam sample <path_population_xml> <path_output_directory> -s <sample_percentage> -v <matsim_version>`. For example, you can use: `pam sample tests/test_data/test_matsim_plansv12.xml tests/test_data/output/sampled -s 0.1` to create a downsampled (to 10%) version of the input (`test_matsim_plansv12.xml`) population.
* combining populations: `pam combine <input_population_1> <input_population_2> <input_population_3...etc> -o <outpath_directory> -m <comment> -v <matsim_version>`.

::: mkdocs-click
    :module: pam.cli
    :command: cli
    :prog_name: pam
    :style: table
    :depth: 1

