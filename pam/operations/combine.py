from pam import core, read


def pop_combine(
    inpaths: str,
    matsim_version: int,
    household_key: str = "hid",
    simplify_pt_trips: bool = False,
    autocomplete: bool = True,
    crop: bool = False,
    leg_attributes: bool = True,
    leg_route: bool = True,
    keep_non_selected=True,
):
    """Combine two or more populations (e.g. household, freight... etc)."""
    print("==================================================")
    print("Combining input populations")

    combined_population = core.Population()

    for inpath in inpaths:
        population = read.read_matsim(
            inpath,
            weight=1,
            version=matsim_version,
            household_key=household_key,
            simplify_pt_trips=simplify_pt_trips,
            autocomplete=autocomplete,
            crop=crop,
            leg_attributes=leg_attributes,
            leg_route=leg_route,
            keep_non_selected=keep_non_selected,
        )
        print(f"population: {population.stats}")

        combined_population += population

    return combined_population
