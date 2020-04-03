# Pandemic Activity Modeller

Modify an existing population activity plan to reflect social and government policy scenarios 
responding to a pandemic.

This work is to aid quick transport demand generation (traditional OD 
matrices and activity based) given new and potential government pandemic related scenarios. It may 
also be useful for other activity based demand modelling 
such as for utility demand.

## Process

1. Build Activity Plans from Travel Diary data (core module)
2. Alter Activity Plans based on Policies regarding (policies module):
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

## Inputs

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
challenge for
 creating activity plans is to **infer** the type of activities between trips (ie home, shopping,
  work). All activity plans are restricted to one day and must start and end with an activity.

### Criteria

There are tests -> the more you can get running as `PASSED` the better you are doing. Run tests 
using pytest, ie:

```
$ pytest -v
========================================================= test session starts =========================================================
platform darwin -- Python 3.7.3, pytest-3.1.2, py-1.8.0, pluggy-0.4.0 -- /Users/fred.shone/.pyenv/versions/3.7.3/bin/python3.7
cachedir: .cache
rootdir: /Users/fred.shone/Projects/pam, inifile:
plugins: mock-1.12.1, cov-2.5.1
collected 23 items

tests/test_1_core.py::test_minutes_to_dt[0-expected0] PASSED
tests/test_1_core.py::test_minutes_to_dt[30-expected1] PASSED
tests/test_1_core.py::test_minutes_to_dt[300-expected2] PASSED
tests/test_1_core.py::test_minutes_to_dt[330-expected3] PASSED
tests/test_1_core.py::test_load PASSED
tests/test_1_core.py::test_agent_pid_0_simple_tour PASSED
tests/test_1_core.py::test_agent_pid_1_simple_tour PASSED
tests/test_1_core.py::test_agent_pid_2_simple_tour PASSED
tests/test_1_core.py::test_agent_pid_3_tour PASSED
tests/test_1_core.py::test_agent_pid_4_complex_tour PASSED
tests/test_2_core_challenge.py::test_agent_pid_5_not_start_from_home FAILED
tests/test_2_core_challenge.py::test_agent_pid_6_not_return_home PASSED
tests/test_2_core_challenge.py::test_agent_pid_7_not_start_and_return_home_night_worker FAILED
tests/test_2_core_challenge.py::test_agent_pid_8_not_start_and_return_home_night_worker_complex_chain_type1 FAILED
tests/test_2_core_challenge.py::test_agent_pid_9_not_start_and_return_home_night_worker_complex_chain_type2 FAILED
tests/test_2_core_challenge.py::test_agent_pid_10_not_start_from_home_impossible_chain_type1 FAILED
tests/test_2_core_challenge.py::test_agent_pid_11_not_start_from_home_impossible_chain_type2 FAILED
tests/test_3_household_policies.py::test_apply_full_hh_quarantine PASSED
tests/test_3_household_policies.py::test_apply_full_person_stay_at_home PASSED
tests/test_3_household_policies.py::test_apply_two_policies PASSED
tests/test_4_activity_policies.py::test_home_education_home_removal_of_education_act PASSED
tests/test_4_activity_policies.py::test_home_education_home_education_home_removal_of_education_act PASSED
tests/test_4_activity_policies.py::test_home_work_home_education_home_removal_of_education_act PASSED
```

As you can see the `tests/test_2_core_challenge.py` tests are failing - the challenge is to get 
as many as these passing without breaking ANY other tests.

### Rules

Clone project and work in your own branch. 

Please work within the `pam.core` module only.

The method that needs modifying is `pam.core.Population.load_from_df()`.

## Quick intro to Travel Diaries and how they relate to Activity Plans

A key component of this project is the conversion of Travel Diaries to Activity Plans. We define 
a Travel Diary as a sequence of travel legs from zone to zone for a given purpose. The Activity 
Plan takes these legs and infers the activity types between. Example activity types are `home`, 
`work`, `education` and so on.

Activity Plan chains can be pretty complex, consider for example a business person attending 
meetings in many different locations. But we always require the plan to last 24 hours and start 
and stop with an activity. We like these start and stop activities to both be the same and ideally 
`home`. We think of this as 'looping', but they don't have to. Night shift workers, for example, 
do not start or end the day at `home`.

When we try to infer activity purpose from trip purpose, we expect a return trip to have the 
same purpose as the outbound trip. But this logic is hard to follow for more complex chains. The test 
cases in `test_2_core_challenge` capture some of the edge cases observed so far.

It is important to note that as a consequence of encoding outbound and return purpose as an 
activity, we never observe a trip purpose as `home`. Luckily we do know the home area from the 
travel diary data (`hzone`). But have to be careful with our logic as travel between different 
activities locations can be intra-zonal.

Activity Plans are represented in this project as regular python `lists()`, containing ordered
`core.Actvities` and `core.Legs`. Plans belong to `core.People` which belong to 
`core.Households`
 which belong to a `core.Population`. For example:

```
population = Population()
household = HouseHold(1)
person = Person(1)

person.add(Activity(1, 'home', 'a'))
person.add(Leg(1, 'car', 'a', 'b'))
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