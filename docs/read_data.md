# Reading data

## Populations

We have some read methods for common input data formats - but first let's take a quick
look at the core pam data structure for populations:

``` python
from pam.core import Population, Household, Person

population = Population()  # initialise an empty population

household = Household('hid0', attributes = {'struct': 'A', 'dogs': 2, ...})
population.add(household)

person = Person('pid0', attributes = {'age': 33, 'height': 'tall', ...})
household.add(person)

person = Person('pid1', attributes = {'age': 35, 'cats_or_dogs?': 'dogs', ...})
household.add(person)

population.print()
```

## Read methods

The first step in any application is to load your data into the core pam format (pam.core.Population). We
are trying to support comon tabular formats ('travel diaries') using `pam.read.load_travel_diary`. A
travel diary can be composed of three tables:

- `trips` (required) -  a trip diary for all people in the population, with rows representing trips
- `persons_attributes` (optional) - optionally include persons attributes (eg: `person income`)
- `households_attributes` (optional) - optionally include households attributes (eg: `hh number of cars`)

The input tables are expected as pandas.DataFrame, eg:
``` python
import pandas as pd
import pam

trips_df = pd.read_csv(trips.csv)
persons_df = pd.read_csv(persons.csv)

# Fix headers and wrangle as required
# ...

population = pam.read.load_travel_diary(
    trips = trips_df,
    persons_attributes = persons_df,
    hhs_attributes = None,
    )

print(population.stats)

example_person = population.random_person
example_person.print()
example_person.plot()
```

PAM requires tabular inputs to follow a basic structure. Rows in the `trips` dataframe represent unique trips by all persons, rows in the
`persons_attributes` dataframe represent unique persons and rows in the `hhs_attributes` dataframe represent unique households. Fields
named `pid` (person ID) and `hid` (household ID) are used to provide unique identifiers to people and households.

**Trips Input:**

eg:

| pid | hid | seq | hzone | ozone | dzone | purp | mode | tst | tet | freq |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | Harrow | Harrow | Camden | work | pt | 444 | 473 | 4.54 |
| 0 | 0 | 1 | Harrow | Camden | Harrow | home | pt | 890 | 919 | 4.54 |
| 1 | 0 | 0 | Harrow | Harrow | Tower Hamlets | work | car | 507 | 528 | 2.2 |
| 1 | 0 | 1 | Harrow | Tower Hamlets | Harrow | home | car | 1065 | 1086 | 2.2 |
| 2 | 1 | 0 | Islington | Islington | Hackney | shop | pt | 422 | 425 | 12.33 |
| 2 | 1 | 1 | Islington | Hackney | Hackney | leisure | walk | 485 | 500 | 12.33 |
| 2 | 1 | 2 | Islington | Croydon | Islington | home | pt | 560 | 580 | 12.33 |


A `trips` table is composed of rows representing unique trips for all persons in the population. Trips must be correctly ordered according to their sequence unless a numeric `seq` (trip sequence) field is provided, in which case trips will be ordered accordingly for each person.

The `trips` input **must** include the following fields:
- `pid` - person ID, used as a unique identifier to associate trips belonging to the same person and to join trips with person attributes if provided.
- `ozone` - trip origin zone ID
- `dzone` - trip destination zone ID
- `mode` - trip mode - note that lower case strings are enforced
- `tst` - trip start time in minutes (integer) or a datetime string (eg: "2020-01-01 14:00:00")
- `tet` - trip end time in minutes (integer) or a datetime string (eg: "2020-01-01 14:00:00")

The `trips` input must **either**:
- `purp` - trip or tour purpose, eg 'work'
- `oact` and `dact` - origin activity type and destination activity type, eg 'home' and 'work'

*Note that lower case strings are enforced and that 'home' activities should be encoded as `home`.*

The `trips` input **may** also include the following fields:
- `hid` - household ID, used as a unique identifier to associate persons belonging to the same household and to join with household attributes if provided
- `freq` - trip weighting for representative population
- `seq` - trip sequence number, if omitted pam will assume that trips are already ordered
- `hzone` - household zone

**'trip purpose' vs 'tour purpose':**

We've encountered a few different ways that trip purpose can be encoded. The preferred way being to encode a trip purpose as being the activity of the destination, so that a trip home would be encoded as `purp = home`. However we've also seen the more complex 'tour purpose' encoding, in which case a return trip from work to home is encoded as `purp = work`. Good news is that the `pam.read.load_travel_diary` will deal ok with either. But it's worth checking.

**Using persons_attributes and /or households_attributes**

eg:

`persons.csv`

| pid | hid | hzone | freq | income| age | driver | cats or dogs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | Harrow | 10.47 | high | high | yes | dogs |
| 1 | 0 | Harrow | 0.034 | low | medium | no | dogs |
| 2 | 1 | Islington | 8.9 | medium | low | yes | dogs |

`households.csv`

| hid | hzone | freq | persons | cars |
| --- | --- | --- | --- | --- |
| 0 | Harrow | 10.47 | 2 | 1 |
| 1 | Islington | 0.034 | 1 | 1 |


If you are using persons_attributes (`persons_attributes`) this table must contain a `pid` field (person ID). If you are using persons_attributes (`households_attributes`) this table must contain a `hid` field (household ID). In both cases, the frequency field `freq` may be used. All other attributes can be included with column names to suit the attribute. Note that `hzone` (home zone) can optionally be provided in the attribute tables.

**A note about 'freq':**

Frequencies (aka 'weights') for trips, persons or households can optionally be added to the respective input tables using columns called `freq`. We generally assume a frequency to represent expected occurances in a full population. For example if we use a person frequency (`person.freq`) the the sum of all these frequencies (`population.size`), will equal the expected population size.

Because it is quite common to provide a person or household `freq` in the trips table, there are two special options (`trip_freq_as_person_freq = True` and `trip_freq_as_hh_freq = True`) that can be used to pass the `freq` field from the trips table to either the people or households table instead.

Generally PAM will assume when you want some weighted output, that it should use household frequencies. If these have not been set then PAM will assume that the household frequency is the average
frequency of persons within the household. If person frequencies are not set the PAM will assume that the person frequency is the average frequency of legs within the persons plan. If you wish to adjust frequencies of a population then you should use the `set_freq()` method, eg:

``` python
factor = 1.2
household.set_freq(household.freq * factor)
for pid, person in household:
    person.set_freq(person.freq * factor)
```

### Read/Write/Other formats

PAM can read/write to tabular formats and MATSim xml (`pam.read.read_matsim` and `pam.write.write_matsim`). PAM can also write to segmented OD matrices using `pam.write.write_od_matrices`.

Benchmark or summary data and cross-tabulations can be extracted with the `pam.write.write_benchmarks` method, passing as arguments the data field(s) to summarise, the dimension(s) to group by, and the aggregation function(s). For example `pam.write_benchmarks(population, dimensions = ['duration_category'], data_fields= ['freq'], aggfunc = [sum]` returns the frequency breakdown of trips' duration. The `write` module also provides a number of wrappers for frequently-used bechmarks under the `write_*****_benchmark` name.

Please get in touch if you would like additional support or feel free to add your own.