# Activity Plans

PAM supports arbitrarily complex chains of activities connected by 'legs' (these are equivalent to 'trips').
The main rules are (i) that plans must consist of sequences of alternate [][pam.activity.Activity] and [][pam.activity.Leg] objects and (ii) that a plan must start and end with an `Activity`:

``` python
from pam.core import Person
from pam.activity import Leg, Activity
from pam

person = Person('Tony', attributes = {'age': 9, 'philosophy': 'stoicism'})

person.add(
    Activity(
        act='home',
        area='zone A',
    )
)

person.add(
    Leg(
        mode='car',
        start_time=utils.parse_time(600),  # (minutes)
        end_time=utils.parse_time(630),
    )
)

person.add(
    Activity(
        act='work',
        area='zone B',
        )
    )

person.add(
    Leg(
        mode='car',
        start_time=utils.parse_time(1800),
        end_time=utils.parse_time(1830),
    )
)

# Continue adding Activities and Legs alternately.
# A sequence must start and end with an activity.
# ...

person.add(
    Activity(
        act='home',
        area='zone B'
    )
)

activities = list(person.plan.activities)
trips = list(person.plan.legs)

person.print()

```

## How travel diaries relate to activity plans

A key component of this project is the conversion of Travel Diaries to Activity Plans.
We define a Travel Diary as a sequence of travel legs from zone to zone for a given purpose over a single day.
The Activity Plan takes these legs and infers the activity types between.
Example activity types are `home`, `work`, `education`, `escort_education` and so on.

Activity Plan chains can be pretty complex, consider for example a business person attending meetings in many different locations and stopping to eat and shop.
We always require the plan to last 24 hours and start and stop with an activity.
We like these start and stop activities to both be the same and ideally `home`.
We think of this as 'looping', but they don't have to.
Night shift workers, for example, do not start or end the day at `home`.

When we try to infer activity purpose from trip purpose, we expect a return trip to have the same purpose as the outbound trip, e.g.:

*trip1(work) + trip2(work) --> activity1(home) + activity2(work) + activity3(home)*

But this logic is hard to follow for more complex chains, eg:

*trip1(work) + trip2(shop) + trip3(work) --> activity1(home) + activity2(work) + activity3(shop) + activity4(home)*

The test cases in `test_3_parse_challenge` capture **some** of the difficult and edge cases observed so far.

It is important to note that as a consequence of encoding outbound and return purpose as an activity, we never observe a trip purpose as `home`.
Luckily we do know the home area from the travel diary data (`hzone`).
But have to be careful with our logic, as travel between different activities locations can be intra-zonal, e.g.:

*activity1(home, zoneA) + activity2(shop, zoneA) + activity2(shop, zoneA)*

Activity Plans are represented in this project as regular python `lists()`, containing **ordered** `activity.Activity` and `activity.Leg` objects.
Plans must start and end with a `activity.Activity`.
Two `activity.Actvity` objects must be separated by a `core.Leg`.

Plans belong to `core.People` which belong to `core.Households` which belong to a `core.Population`. For example:

``` python
from pam.core import Population, Household, Person
from pam.activity import Activity, Leg

population = Population()  # init
household = Household(hid=1)  # hid is household id
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

## A note on the pain of wrapping

Activity Plans often enforce that a plan returns to the same activity (type and location) that they started at.
Furthermore they sometimes enforce that this activity be `home`.
Such plans can be thought of as wrapping plans.
Where the last and first activity can be though of as linked.
This need not be a `home` activity, for example in the case of night workers.

We have encountered many variations of sequences for plans, including wrapping and wrapping.
Although they are generally edge cases, they exists and generally represent real people.
We are therefore endeavoring to support all these cases in our plan modifiers.
This is resulting some difficult to follow logic (e.g., [][pam.activity.Plan.fill_plan]).

## Plan cropping
The [`pam.operations.cropping`](reference/pam/operations/cropping.md) module allows to spatially subset populations, by simplifying plan components that take place outside the "core" area.
Any activities or legs that do not affect that core area are removed from the agents' plans, and agents with fully-external plans are removed from the population.
Examples of using the module can be found in the [][plan-cropping] notebook.