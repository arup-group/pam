import pytest
import numpy as np
from pam.planner import clustering
from pam.read import read_matsim
from tests.fixtures import population_heh
import os

test_plans = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 "test_data/test_matsim_plansv12.xml")
)


@pytest.fixture
def population():
    population = read_matsim(test_plans, version=12)
    return population


def test_identical_stings_have_zero_distance():
    assert clustering._levenshtein_distance('aa', 'aa') == 0


def test_completely_different_stings_have_distance_one():
    assert clustering._levenshtein_distance('aa', 'bb') == 1


def test_substitution_costs_one():
    assert clustering._levenshtein_distance('aa', 'ab') == 0.5
    assert clustering._levenshtein_distance('ba', 'aa') == 0.5


def test_distance_matrix_is_summetrical():
    sequences = ['aa', 'bb']
    dist_matrix = clustering.calc_levenshtein_matrix(
        x=sequences,
        y=sequences
    )

    assert dist_matrix[0, 0] == 0
    assert dist_matrix[0, 1] == clustering._levenshtein_distance(*sequences)
    np.testing.assert_array_almost_equal(dist_matrix.T, dist_matrix)


def test_clustering_create_model(population):
    clusters = clustering.PlanClusters(population)
    n_clusters = 2
    assert clusters.model is None
    clusters.fit(n_clusters=n_clusters)
    assert set(clusters.model.labels_) == set([0, 1])


def test_closest_matches_return_different_plan(population):
    clusters = clustering.PlanClusters(population)
    plan = population['chris']['chris'].plan
    closest_plans = clusters.get_closest_matches(plan, 3)
    for closest_plan in closest_plans:
        assert plan != closest_plan


def test_closest_matches_are_ordered_by_distance(population):
    clusters = clustering.PlanClusters(population)
    plan = population['chris']['chris'].plan
    plan_encoded = clusters.plan_encoder.encode(plan)
    closest_plans = clusters.get_closest_matches(plan, 3)
    dist = 1
    for closest_plan in closest_plans[::-1]:
        dist_match = clustering._levenshtein_distance(
            plan_encoded,
            clusters.plan_encoder.encode(closest_plan)
        )
        assert dist_match <= dist
        dist = dist_match 


def test_cluster_plans_match_cluster_sizes(population):
    clusters = clustering.PlanClusters(population)
    n_clusters = 2
    clusters.fit(n_clusters=n_clusters)
    cluster_sizes = clusters.get_cluster_sizes()
    for cluster, size in cluster_sizes.items():
        assert len(clusters.get_cluster_plans(cluster)) == size
    assert cluster_sizes.sum() == len(clusters.plans)
