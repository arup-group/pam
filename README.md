# Policy Activity Modeller

Modify an existing population activity plan to reflect government policy scenarios around social 
distancing.

This work is to aid quick transport demand generation (traditional OD 
matrices and activity based) given new and potential government pandemic related scenarios. It may 
also be useful for other activity based demand modelling 
such as for utility demand.

## Process

1. Build activity plans from trip data (mimi can do this)
2. Alter Activity Plans based on Policies regarding:
    1. activity from persons ill and/or self isolating
    2. education activities
    3. work activities
    4. shopping activities
    5. discretionary activities
3. Review changes to population activities (ie check summary statistics)
4. Rebuild trip data format from altered activity plans
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

## Inputs

### Activity Plans

Tabular data with each row describing a unique trip from an origin (assumed home at start of day)
 to destination. trips are uniquelly identified by person ids and ordered by sequence number. 
 Trips are labelled with purpose, 
 
 This is based on the [LTDS](https://www.clocs.org.uk/wp-content/uploads/2014/05/london-travel-demand-survey-2011.pdf)
 
 #### Required fields:
`pid` - person ID
`hid` - household ID
`tid` - trip id
`tseqno` - trip sequence number
`hzone` - household zone, Lower Super Output Area (LSOA)
`dpurp` - trip purpose
`mdname` - trip mode
`tstime` - trip start time (clock)
`tetime` - trip end time (clock)
or `tstimei` - trip end time (minutes)
or `tetimei` - trip end time (minutes)
`freq` - weighting for representative population

### Persons

Tabular data describing socio-economic characteristics for each person.

 #### Required fields:
`pid` - person ID
`hsize` - household size
`car` - number of cars owned by household
`inc` - income group
`hstr` - household structure
`gender` - male/female only?
`age` - age group
`race` - ethnicity
`license` - yes/no/unknown
`job` - full-time/part-time/education/retired/unknown
`occ` - occupation group
