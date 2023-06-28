from pam.samplers.population import sample


def test_upsample_from_hh_weights(population_heh):
    population = population_heh
    # set hh weights
    for _, hh in population:
        hh.hh_freq = 1
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_hh_weights_down_sample(population_heh):
    population = population_heh
    # set hh weights
    for _, hh in population:
        hh.hh_freq = 2
    new_population = sample(population=population, sample=0.5, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_hh_weights_up_sample(population_heh):
    population = population_heh
    # set hh weights
    for _, hh in population:
        hh.hh_freq = 2
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population) / 2
    assert population.size == new_population.size


def test_upsample_from_person_weights(population_heh):
    population = population_heh
    # set person weights
    for _, _, p in population.people():
        p.person_freq = 1
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_person_weights_down_sample(population_heh):
    population = population_heh
    # set person weights
    for _, _, p in population.people():
        p.person_freq = 2
    new_population = sample(population=population, sample=0.5, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_person_weights_up_sample(population_heh):
    population = population_heh
    # set person weights
    for _, _, p in population.people():
        p.person_freq = 2
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population) / 2
    assert population.size == new_population.size


def test_upsample_from_leg_weights(population_heh):
    population = population_heh
    # set leg weights
    for _, _, p in population.people():
        for leg in p.legs:
            leg.freq = 1
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_leg_weights_down_sample(population_heh):
    population = population_heh
    # set leg weights
    for _, _, p in population.people():
        for leg in p.legs:
            leg.freq = 2
    new_population = sample(population=population, sample=0.5, verbose=False, seed=0)
    assert len(population) == len(new_population)
    assert population.size == new_population.size


def test_upsample_from_leg_weights_up_sample(population_heh):
    population = population_heh
    # set leg weights
    for _, _, p in population.people():
        for leg in p.legs:
            leg.freq = 2
    new_population = sample(population=population, sample=1, verbose=False, seed=0)
    assert len(population) == len(new_population) / 2
    assert population.size == new_population.size
