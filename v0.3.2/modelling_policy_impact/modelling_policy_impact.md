# Modelling the impact of policies on populations

PAM uses **policies** to model change to a population.
For example, based on social distancing requirements we might want to reflect that people are expected to make less shared shopping trips or tours.
We can do this using the following policy, if you want to define the policy from first principles:

``` python
policy_reduce_shopping_activities = HouseholdPolicy(
        ReduceSharedActivity(['shop', 'shop_food']),
        ActivityProbability(['shop', 'shop_food'], 1)
)
```

There exists a convenience class for this policy and an equivalent policy can be defined in the following way:

``` python
policy_reduce_shopping_activities = ReduceSharedHouseholdActivities(
        ['shop', 'shop_food'],
        ActivityProbability(['shop', 'shop_food'], 1)
)
```

This policy removes all but one the household's shared shopping tours:

![PAM-policy-example](resources/PAM-policy-example.png)

In general, a policy is defined in the following way:

1. You first select the level at which is should be applied:
    - [HouseholdPolicy][pam.policy.policies.HouseholdPolicy]
    - [PersonPolicy][pam.policy.policies.PersonPolicy]
    - [ActivityPolicy][pam.policy.policies.ActivityPolicy]
2. You then select the modifier, which performs the actions to a person's activities
    - [RemoveActivity][pam.policy.modifiers.RemoveActivity]
    - [ReduceSharedActivity][pam.policy.modifiers.ReduceSharedActivity]
    - [MoveActivityTourToHomeLocation][pam.policy.modifiers.MoveActivityTourToHomeLocation]
3. Finally, you give a likelihood value with which the policy should be applied with.
    You have a few choices here:
    - a number greater than 0 and less or equal to 1.
    This will be understood to be at the level at which the policy is applied.
    E.g. `#!python PersonPolicy(RemoveActivity(['work']), 0.5)` will give each person a fifty-fifty chance of having their work activities removed.

    - you can explicitly define at which level a number greater than 0 and less or equal to 1 will be applied.
    E.g. `#!python HouseholdPolicy(RemoveActivity(['work']), PersonProbability(0.5))` will apply a probability of 0.5 per person in a household, and apply the policy to all persons within a household if selected.

    - you can also pass a function that operates on a [Household][pam.core.Household], [Person][pam.core.Person] or [Activity][pam.activity.Activity] object and returns a number between 0 and 1.
    E.g. if our function is:
    ``` python
    def sampler(person):
        if person.attributes['key_worker'] == True:
            return 0
        else:
            return 1
    ```
    we can define `#!python PersonPolicy(RemoveActivity(['work']), PersonProbability(sampler))` which will remove all work activities from anyone who is not a 'key_worker'

    - you can choose from:
        - `HouseholdProbability`
        - `PersonProbability`
        - `ActivityProbability`

PAM allows multiple of such policies to be combined to build realistic and complex scenarios. Leveraging activity plans means that PAM can implement detailed policies that are dependent on:

- person attributes
- household attributes
- activity types
- travel modes
- times
- spatial locations
- sequences such as tours
- any combination of the above

A full overview of policies and examples of the policies available are [detailed in this example][modifying-the-population-using-simple-policies].

## Example modifiers/policies:

### Ill and self-quarantined

- Person quarantine based on age
- Household quarantine based on household members

### Education activities

Remove or reduce education based tours/trips including escorts:

- Remove education activities based on age
- Maintain education for 'care-constrained' households (critical workers)

### Work activities

- Furlough and unemployment based on sector
- Work from home based on sector
- Increase or reduce activities and activity durations based on sector

### Shopping activities

- Remove or reduce discretionary shopping
- Reduce food shopping
- Remove shared tours
- Move tours closer to home

### Discretionary activities

- Remove or reduce discretionary activities such as leisure
- Move tours closer to home
- Select the location of discretionary activities, in relation to "anchor"/"mandatory" activities

## In-progress modifiers/policies

Logic also be added to apply:

- mode shift
- location shift
- times
- durations