# Non-coding contributions

## Literature review

We still need validation of the overall approach.
Much of the methodology (detailed in this document) is based on what can pragmatically be done, not what theoretically should be done.
We'd appreciate links to relevant papers.
Or even better we'd love a lit review - we'll add it to this document.

## Research

We need help with designing useful features, applying them to real problems.
As part of this we need:

### Evidence and data for validation

We know, for example, that many people have removed certain activities from their daily plans, such as to school or university.
But we don't know how many.
We'd like help finding and eventually applying **validation data** such as recent [change in mobility](https://www.google.com/covid19/mobility/).

### Evidence for new features

We currently support the following activity plan modifications:

- probabilistic removal of all activities, i.e., full quarantine or isolation
- probabilistic removal of specific activities, i.e., education
- automatic extension of other (typically staying at home) activities

But we'd like help to **find evidence** for other modifications that we think are occurring:

- changing duration of an activity
- moving activity closer to home, i.e., shopping trips
- changing travel choice, i.e., mode
- moving home location (i.e., national and local emigration)
- household shared activities/no longer shared activities, such as leisure
- defining key workers

### Evidence for technical methodology

Modifying a plan to remove an activity can cascade into other changes.
In the case of people with complex chains of activities, the removal of a single activity requires adjustments to the remainder.
Do people leave later of earlier if they have more time for example?
The methods for this logic is in [pam.core].People.