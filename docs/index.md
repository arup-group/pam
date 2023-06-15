# Population Activity Modeller (PAM)

PAM is a python API for activity sequence modelling. Primary features:

- common format read/write including MATSim xml
- sequence inference from travel diary data
- rules based sequence modification
- sequence visualisation
- facility sampling
- research extensions

PAM was originally called the "Pandemic Activity Modifier". It was built in response to COVID-19, to better and more quickly update models for behaviour changes from lockdown policies than existing aggregate models.

 ![PAM](resources/PAM-motivation.png)

**Who is this for?** PAM is intended for use by any modeller or planner using trip diary data or activity plans.
**What can this do?** PAM provides an API and examples for modifying activity plans, for example, based on COVID-19 lockdown scenarios.

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

## Why Activity Plans?

 ![example-activity-plans](resources/example-activity-plans.png)

1. They are the ideal mechanism for applying changes, allowing for example,
consideration of joint dis-aggregate features across an entire day.

2. They can be post processed for many other output formats such as origin-destination matrices or activity diaries. These outputs can the be used in many different
applications such as transport, utility demand, social impact and so on.