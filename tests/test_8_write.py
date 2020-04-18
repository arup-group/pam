import os
import pytest

from .fixtures import population_heh
from pam.write import write_matsim, write_matsim_plans, write_matsim_attributes
from pam.parse import read_matsim


def test_write_plans_xml(tmp_path, population_heh):
	location = str(tmp_path / "test.xml")
	write_matsim_plans(population_heh, location=location, comment="test")


def test_write_plans_gzip(tmp_path, population_heh):
	location = str(tmp_path / "test.xml.gz")
	write_matsim_plans(population_heh, location=location, comment="test")


def test_write_attributes_xml(tmp_path, population_heh):
	location = str(tmp_path / "test.xml")
	write_matsim_attributes(population_heh, location=location, comment="test")


def test_write_attributes_gzip(tmp_path, population_heh):
	location = str(tmp_path / "test.xml.gz")
	write_matsim_attributes(population_heh, location=location, comment="test")


def test_write_read_continuity_xml(tmp_path, population_heh):
	plans_location = str(tmp_path / "test_plans.xml")
	write_matsim_plans(population_heh, location=plans_location, comment="test")
	attributes_location = str(tmp_path / "test_attributes.xml")
	write_matsim_attributes(population_heh, location=attributes_location, comment="test")
	population = read_matsim(
		plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
	)
	assert population_heh['0']['1'].plan == population['0']['1'].plan


def test_write_read_continuity_gzip(tmp_path, population_heh):
	plans_location = str(tmp_path / "test_plans.xml.gz")
	write_matsim_plans(population_heh, location=plans_location, comment="test")
	attributes_location = str(tmp_path / "test_attributes.xml.gz")
	write_matsim_attributes(population_heh, location=attributes_location, comment="test")
	population = read_matsim(
			plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
	)
	assert population_heh['0']['1'].plan == population['0']['1'].plan


test_trips_path = os.path.abspath(
	os.path.join(os.path.dirname(__file__), "test_data/test_matsim_plans.xml")
)
test_attributes_path = os.path.abspath(
	os.path.join(os.path.dirname(__file__), "test_data/test_matsim_attributes.xml")
)

def test_read_write_read_continuity_complex_xml(tmp_path):
	population_in = read_matsim(test_trips_path, test_attributes_path)
	complex_plan_in = population_in['census_1']['census_1'].plan

	plans_location = str(tmp_path / "test_plans.xml")
	write_matsim_plans(population_in, location=plans_location, comment="test")
	attributes_location = str(tmp_path / "test_attributes.xml")
	write_matsim_attributes(population_in, location=attributes_location, comment="test")

	population_out = read_matsim(
		plans_path=plans_location, attributes_path=attributes_location, household_key='hid'
	)
	complex_plan_out = population_out['census_1']['census_1'].plan

	assert complex_plan_in == complex_plan_out
	