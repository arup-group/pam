# Pandemic Activity Modifier (PAM)

Our day to day activities have been rapidly shifted by recent policies and behavioural 
changes related to the COVID-19 pandemic. If we want to better plan existing and near-term 
scenarios (for transport systems and other sectors) - existing models need to be updated and new scenarios generated quickly.

**Who is this for?** PAM is intended for use by any modeller or planner using trip diary data or activity plans.
**What can this do?** PAM provides an API and examples for modifying activity plans based on COVID-19 scenarios.

You can read about PAM on medium [here](https://medium.com/arupcitymodelling/pandemic-activity-modifier-intro-3d2dccbc716e).

 ## Features

This project is not a new activity model. Instead it to seeks to adjust existing activity 
representations, already derived from exiting models or survey data:

 ![PAM](resources/PAM-features.png)

(i) **Read/Load** input data (eg travel diary) to household and person Activity Plans.

(ii) **Modify** the Activity Plans for new social and government policy scenarios (eg 
remove education activities for non key worker households). Crucially PAM facilitates 
application of detailed policies at the person and household level, while still respecting 
the logic of arbitrarily complex activity chains.

(iii) **Output** to useful formats for activity based models or regular transport models. Facilitate preliminary **Analysis** and **Validation** of changes.

This work is primarily intended for transport modellers, to make quick transport demand
scenarios. But it may also be useful for other activity based demand modelling such as for goods 
supply or utility demand.
 
## Contents

- Installation
- Why Activity Plans?
- Modelling the pandemic
- Example modifiers/policies
- Input/output data formats 
- Get involved
- Technical notes

## Installation

Assuming python ~3.7 and using git:

```
git clone git@github.com:arup-group/pam.git
cd pam
pip install -r requirements.txt
pip install -e .
```

We known that requirements are already available in a up to date Anaconda installation.

## Why Activity Plans?

 ![example-activity-plans](resources/example-activity-plans.png) 

1. They are the ideal mechanism for applying changes, allowing for example, 
consideration of joint dis-aggregate features across an entire day.

2. They can be post processed for many other output formats such as origin-destination matrices or activity diaries. These outputs can the be used in many different 
applications such as transport, utility demand, social impact and so on.

## Modelling the pandemic

PAM uses **policies** to model change to a population. For example, based on social distancing requirements we might 
want to reflect that people are expected to make less shared shopping trips or tours. We can do this using the 
following policy:
```
policy_reduce_shopping_activities = HouseholdPolicy(
        ReduceSharedActivity(['shop', 'shop_food']), 
        ActivityProbability(['shop', 'shop_food'], 1)
)
```
if you want to define the policy from first principles. There exists a convenience class for this policy and
an equivalent policy can be defined in the following way:
```
policy_reduce_shopping_activities = ReduceSharedHouseholdActivities(
        ['shop', 'shop_food'], 
        ActivityProbability(['shop', 'shop_food'], 1)
)
```
This policy removes all but one the household's shared shopping tours:

![PAM-policy-example](resources/PAM-policy-example.png)

In general, a policy is defined in the following way:

- You first select the level at which is should be applied:
    - `HouseholdPolicy`
    - `PersonPolicy`
    - `ActivityPolicy`
- You then select the modifier, which performs the actions to a person's activities
    - `RemoveActivity`
    - `ReduceSharedActivity`
    - `MoveActivityTourToHomeLocation`
- Finally, you give a likelihood value with which the policy should be applied with. You have a few choices here:
    - a number greater than 0 and less or equal to 1. This will be understood to be at the level at which the policy 
    is applied. 
        - E.g. `PersonPolicy(RemoveActivity(['work']), 0.5)` will give each person a fifty-fifty chance of having
    their work activities removed.
    - you can explicitly define at which level a number greater than 0 and less or equal to 1 will be applied by passing:
        - E.g. `HouseholdPolicy(RemoveActivity(['work']), PersonProbability(0.5))` will apply a probability of 0.5
        per person in a household, and apply the policy to all persons within a household if selected.
    - you can also pass a function that operates on a `core.Household`, `core.Person` or `core.Activity` object and
    returns a number between 0 and 1.
        - E.g. if
        ```
        def sampler(person):
            if person.attributes['key_worker'] == True:
                return 0
            else:
                return 1
        ```
        we can define `PersonPolicy(RemoveActivity(['work']), PersonProbability(sampler))` which will remove all work 
        activities from anyone who is not a 'key_worker'
    - you can choose from:
        - `HouseholdProbability`
        - `PersonProbability`
        - `ActivityProbability` 

PAM allows multiple of such policies to be combined to build realistic and complex scenarios. Leveraging activity plans means that PAM can implement detailed policies that are dependant on:
- person attributes
- household attributes
- activity types
- travel modes
- times
- spatial locations
- sequences such as tours
- any combination of the above

A full overview of policies and examples of the policies available are [detailed in this notebook](https://github.com/arup-group/pam/blob/master/notebooks/PAM%20Policies%20walk-through.ipynb).

## Example modifiers/policies:   

##### Ill and self-quarantined

- Person quarantine based on age
- Household quarantine based on household members

##### Education activities

Remove or reduce education based tours/trips including escorts:

- Remove education activities based on age
- Maintain education for 'care-constrained' households (critical workers)

##### Work activities

- Furlough and unemployment based on sector
- Work from home based on sector
- Increase or reduce activities and activity durations based on sector

##### Shopping activities

- Remove or reduce discretionary shopping
- Reduce food shopping
- Remove shared tours
- Move tours closer to home

##### Discretionary activities

- Remove or reduce discretionary activities such as leisure
- Move tours closer to home

##### In progress

Logic also be added to apply:

- mode shift
- location shift
- times
- durations





## Input/output data formats

We primarily expect to support tabular input the form of a travel diary and person attributes as 
described below. However we also support tabular activity plans formats and MATSim xml.

#### Travel diary

Tabular data with each row describing a unique trip from an origin (assumed home at start of day)
 to destination. trips are uniquely identified by person ids and ordered by sequence number. 
 Trips are labelled with home, origin, and destination zones, purpose, mode, start time, end 
 time and some form of weighting:
  
**Required fields:**
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

#### Persons data

Tabular data describing socio-economic characteristics for each person. For example:

**Recommended fields:**
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

## Get involved

Our goals:

- Theoretical Quality: Expert driven features with research and open case studies.
- Feature Quality: Broadly useful and extendable features with good documentation and some testing.

Less abstractly, there are a good number of **coding** and **non-coding** tasks to chip in 
with:

### Give feedback
Read through this document, let us know what you think, share. Feedback gladly received as an 
[issue](https://github.com/arup-group/pam/issues), on 
[slack](https://join.slack.com/share/I011QU6NN9J/3jAlIBVEbvNln55kGvtZv6ML/zt-dih8pklw-nOPgRzbL3SKj5coH9xemFA)
 or you can email fred.shone@arup.com.
    
### Literature review
We still need validation of the overall approach. Much of the methodology (detailed in this 
document) is based on what can pragmatically be done, not what theoretically should be done. We'd
 appreciate links to relevant papers. Or even better we'd love a lit review - we'll add it to 
 this document.
 
### Research

We need help with designing useful features, applying them to real problems. As part of this we 
need:

#### Evidence and data for validation
We know, for example, that many people have removed certain 
activities from their daily plans, such as to school or university. But we don't know how many. We'd 
like help finding and eventually applying **validation data** such as recent [change in 
mobility](https://www.google.com/covid19/mobility/). 

#### Evidence for new features

We currently support the following activity plan modifications:

- probabilistic removal of all activities, ie full quarantine or isolation
- probabilistic removal of specific activities, ie education
- automatic extension of other (typically staying at home) activities

But we'd like help to **find evidence** for other modifications that we think are occurring:

- changing duration of an activity
- moving activity closer to home, ie shopping trips
- changing travel choice, ie mode
- moving home location (ie national and local emigration)
- household shared activities/no longer shared activities, such as leisure
- defining key workers

#### Evidence for technical methodology
    
Modifying a plan to remove an activity can cascade into other changes. In the case of 
people with complex chains of activities, the removal of a single activity requires adjustments 
to the remainder. Do people leave later of earlier if they have more time for example? The 
methods for this logic is in `pam.core.People`.

### The code

For a quick start at the code, checkout the 
[getting started notebook/s](https://github.com/arup-group/pam/tree/master/notebooks).

#### Test
If you've come this far - please consider cloning this repo, follow the installation instructions
 run the tests and maybe try out any example notebooks.
 
#### Dev
We maintain a backlog of tasks, please in touch if you would like to contribute - or raise your own issue.

We need help to **go faster**. We expect to deal with populations in the tens of millions. We would 
like help with profiling and implementing parallel compute.

Please branch as you wish but please get in touch first ([issue](https://github.com/arup-group/pam/issues), 
[slack](https://join.slack.com/share/I011QU6NN9J/3jAlIBVEbvNln55kGvtZv6ML/zt-dih8pklw-nOPgRzbL3SKj5coH9xemFA))
.

### Use cases
We will share open and dummy data where available, we would love people to do some experiments 
and develop some viz and validation pipelines. Any example notebooks can be added to the example
[notebooks](https://github.com/arup-group/pam/tree/master/notebooks).

Help gladly received as an 
[issue](https://github.com/arup-group/pam/issues), on 
[slack](https://join.slack.com/share/I011QU6NN9J/3jAlIBVEbvNln55kGvtZv6ML/zt-dih8pklw-nOPgRzbL3SKj5coH9xemFA)
 or you can email fred.shone@arup.com.
 

## Technical notes

#### Intro to travel diaries and how they relate to activity plans

A key component of this project is the conversion of Travel Diaries to Activity Plans. We define 
a Travel Diary as a sequence of travel legs from zone to zone for a given purpose over a single 
day. The Activity Plan takes these legs and infers the activity types between. Example activity 
types are `home`, `work`, `education`, `excort_education` and so on.

Activity Plan chains can be pretty complex, consider for example a business person attending 
meetings in many different locations and stopping to eat and shop. We always require the plan
 to last 24 hours and start 
and stop with an activity. We like these start and stop activities to both be the same and ideally 
`home`. We think of this as 'looping', but they don't have to. Night shift workers, for example, 
do not start or end the day at `home`.

When we try to infer activity purpose from trip purpose, we expect a return trip to have the 
same purpose as the outbound trip, eg:

*trip1(work) + trip2(work) --> activity1(home) + activity2(work) + activity3(home)*

But this logic is hard to follow for more complex chains, eg:

*trip1(work) + trip2(shop) + trip3(work) --> activity1(home) + activity2(work) + activity3(shop) +
 activity4(home)*

The test cases in `test_3_parse_challenge` capture **some** of the difficult and edge cases observed
 so far.

It is important to note that as a consequence of encoding outbound and return purpose as an 
activity, we never observe a trip purpose as `home`. Luckily we do know the home area from the 
travel diary data (`hzone`). But have to be careful with our logic, as travel between different 
activities locations can be intra-zonal, eg:

*activity1(home, zoneA) + activity2(shop, zoneA) + activity2(shop, zoneA)*

Activity Plans are represented in this project as regular python `lists()`, containing **ordered**
`activity.Activity` and `activity.Leg` objects. Plans must start and end with a 
`activity.Activity`. Two `activity.Actvity` objects must be seperated by a `core.Leg`.

Plans belong to `core.People` which belong to 
`core.Households` which belong to a `core.Population`. For example:

```
from pam.core import Population, Household, Person
from pam.activity import Activity, Leg

population = Population()  # init
household = HouseHold(hid=1)  # hid is household id
person = Person(pid=1)  # pid is person id
person.add(
    Activity(seq=1, act='home', area='a', start_time=0, end_time=450)  # time in minutes
)
person.add(
    Leg(seq=1, mode='car', start_area='a', end_area='b', start_time=450, end_time=480)
)
person.add(
    Activity(2, 'work', 'b', 480, 880)
)
person.add(
    Leg(2, 'car', 'b', 'a', 880, 900)
)
person.add(
    Activity(3, 'home', 'a', 900, 24*60-1)  # last activity must end at 23:59(:59)
)
household.add(person)
population.add(household)
```

#### A note on the pain of wrapping

Activity Plans often enforce that a plan returns to the same activity (type and location) that 
they started at. Furthermore they sometimes enforce that this activity be `home`. Such plans can 
be thought of as wrapping plans. Where the last and first activity can be though of as linked. 
This need not be a `home` activity, for example in the case of night workers.

We have encountered many variations of sequences for plans, including wrapping and wrapping. 
Although they are generally edge cases, they exists and generally represent real people. We are 
therefore endeavoring to support all these cases in our plan modifiers. This is resulting some 
difficult to follow logic (eg `pam.activity.Plan.fill_plan()`).

 ![PAM](resources/PAM-motivation.png)