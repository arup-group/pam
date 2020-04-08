# Pandemic Activity Modeller

(i) Convert a standard population **travel diary** survey to **activity plans**, (ii) Modify the 
activity plans to reflect social and government policy scenarios, (iii) Output
 the adjusted plans to useful formats for activity based models or regular transport models.

This work is to aid quick transport demand generation (traditional OD 
matrices and activity based) given new and potential government pandemic related scenarios. It may 
also be useful for other activity based demand modelling 
such as for goods supply or utility demand.

## Get Involved

We would like to develop this project as quickly as possible to assist with pandemic and 
post-pandemic decision making. This project has two primary goals:

- Feature Quality: Broadly useful and extendable features with good documentation and testing.
- Theoretical Quality: Expert driven features with research and open case studies.

Less abstractly, there are a good number of technical and non-technical of tasks to chip in with:
1. Early feedback - read through this document, let us know what you think, share.
2. Test - install our project, run the tests, try the code/notebooks, let us know if it breaks.
3. Literature Review - we need validation of the overall approach.
4. Use Cases - thought of a good use case? Let us know.
4. Research - 


## Process Overview

1. Build Activity Plans from Travel Diary data
2. Alter Activity Plans based on Policies regarding:
    1. activity from persons ill and/or self isolating
    2. education activities
    3. work activities
    4. shopping activities
    5. discretionary activities
3. Review changes to population activities (ie check summary statistics)
4. Rebuild Travel Diary format from altered activity plans
5. Convert to O-D matrices if required

## Policy Mechanisms:   

Once we have a representation of activity plans for the population, we can seek to adjust these 
plans based on pandemic based policies. This will use statistical rules dependant on agent 
plans and attributes.

### Ill and self-quarantined

Reduce overall activities by removing the entirety of an individual's or household's plans, based on 
rates of illness, specifically causing hospitalisation or self-isolation.

Baseline sickness rate is [~2%](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/labourproductivity/articles/sicknessabsenceinthelabourmarket/2018).
This will already be reflected in plans. Note that any adjustment to this rate needs to be 
applied with consideration of new WFH rate?

### Education Activities

Remove education based tours/trips including escorts:

School - critical workers only
University - mostly closed

### Work Activities

Advice is to work from home where possible - this will effect different occupations differently.

Also likely to remove many discretionary activities that were otherwise included in work based 
tours.

### Shopping Activities

Guidance is to reduce shopping activities. Additionally existing shopping activities as part of 
another tour (such as work tour)is likely to change to a simple home based tour.

### Discretionary Activities

Current guidance is to remove discretionary activities, although it is not clear if or how 
exercise can be considered.

## Validation

Generally we are assuming that PAM will be useful when (i) existing disaggregated travel surveys 
are suddenly inaccurate - for example after a sharp change in behaviour, or (ii) where rapid 
activity modelling is required.

For case (i) it will still be possible to carry out some validation - most likely through 
benchmarking against aggregate statistics such as 
[change in mobility](https://www.google.com/covid19/mobility/).

## Project Structure

1. The `core` module holds activity plan classes (`Population`, `Household`, `Person`, `Activity`
 and `Leg`) and general methods.
2. The `parse` module is responsible for building activity plans from travel diary data.
3. The `modify` module is responsible for applying activity modifications.

## Input Data Formats

### Travel Diary

Tabular data with each row describing a unique trip from an origin (assumed home at start of day)
 to destination. trips are uniquely identified by person ids and ordered by sequence number. 
 Trips are labelled with home, origin, and destination zones, purpose, mode, start time, end 
 time and some form of weighting:
  
 #### Required fields:
- `pid` - person ID
- `hid` - household ID
- `seq` - trip sequence number
- `hzone` - household zone
- `ozone` - trip origin zone
- `dzone` - trip destination zone
- `purp` - trip purpose
- `mode` - trip mode
- `tst` - trip start time (minutes)
- `tet` - trip end time (minutes)
- `freq` - weighting for representative population

### Persons Data

Tabular data describing socio-economic characteristics for each person. For example:

 #### Recommended fields:
- `pid` - person ID
- `hsize` - household size
- `car` - number of cars owned by household
- `inc` - income group
- `hstr` - household structure
- `gender` - eg male/female/unknown
- `age` - age group
- `race` - ethnicity
- `license` - eg yes/no/unknown
- `job` - eg full-time/part-time/education/retired/unknown
- `occ` - occupation group

## Challenge

The `pam.core` module loads up Travel Diaries to create Activity Plans. At the moment loading up 
simple plans (ie those that start and end at home is easy). But for non standard plans, such as 
those belonging to night workers, that don't start and end from home, the logic can break.

Dummy Travel Plans data can be found in `pam/tests/test_data/simple_travel_diaries.csv`. The 
challenge for creating activity plans is to **infer** the type of activities between trips (ie 
home, shopping, work). All activity plans are restricted to one day and must start and end with 
an activity.

### Criteria

There are tests -> the more you can get running as `PASSED` the better you are doing. Run tests 
using pytest, ie:

```
$ pytest -v
```

You should find some tests in `tests/test_3_parse_challenge.py` are failing. This challenge set of 
tests represents edge cases for the standard travel diary parser: `pam.parse.load_from_dfs()` - the 
challenge is to adjust `pam.parse.load_from_dfs()` to get as many tests passing without breaking
 ANY test modules.

### Rules

Clone project and work in your own branch. 

Please work within the `pam.parse` module only.

## Quick intro to Travel Diaries and how they relate to Activity Plans

A key component of this project is the conversion of Travel Diaries to Activity Plans. We define 
a Travel Diary as a sequence of travel legs from zone to zone for a given purpose over a single 
day. The Activity Plan takes these legs and infers the activity types between. Example activity 
types are `home`, `work`, `education` and so on.

Activity Plan chains can be pretty complex, consider for example a business person attending 
meetings in many different locations. But we always require the plan to last 24 hours and start 
and stop with an activity. We like these start and stop activities to both be the same and ideally 
`home`. We think of this as 'looping', but they don't have to. Night shift workers, for example, 
do not start or end the day at `home`.

When we try to infer activity purpose from trip purpose, we expect a return trip to have the 
same purpose as the outbound trip. But this logic is hard to follow for more complex chains. The test 
cases in `test_3_parse_challenge` capture some of the difficult and edge cases observed so far.

It is important to note that as a consequence of encoding outbound and return purpose as an 
activity, we never observe a trip purpose as `home`. Luckily we do know the home area from the 
travel diary data (`hzone`). But have to be careful with our logic as travel between different 
activities locations can be intra-zonal.

Activity Plans are represented in this project as regular python `lists()`, containing ordered
`core.Actvity` and `core.Leg` objects. Plans belong to `core.People` which belong to 
`core.Households` which belong to a `core.Population`. For example:

```
population = Population()
household = HouseHold(hid=1)  # hid is household id
person = Person(pid=1)  # pid is person id

person.add(Activity(seq=1, act='home', area='a'))
person.add(Leg(seq=1, mode='car', start_area='a', 'b'))
person.add(Activity(2, 'work', 'b'))
person.add(Leg(2, 'car', 'b', 'a'))
person.add(Activity(3, 'home', 'a'))

household.add(person)
population.add(household)
```

### Installation

WIP

assuming python ~3.7

git clone this repo

`cd pam`

`pip install -r requirements.txt` (or just get pandas and pytest working)