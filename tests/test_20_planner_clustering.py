import numpy as np
import pytest
from pam.planner import clustering


@pytest.fixture
def clusters(population_no_args):
    clusters = clustering.PlanClusters(population_no_args)
    n_clusters = 2
    clusters.fit(n_clusters=n_clusters)
    return clusters


def test_identical_stings_have_zero_distance():
    assert clustering._levenshtein_distance("aa", "aa") == 0


def test_completely_different_stings_have_distance_one():
    assert clustering._levenshtein_distance("aa", "bb") == 1


def test_substitution_costs_one():
    assert clustering._levenshtein_distance("aa", "ab") == 0.5
    assert clustering._levenshtein_distance("ba", "aa") == 0.5


def test_distance_matrix_is_summetrical():
    sequences = ["aa", "bb"]
    dist_matrix = clustering.calc_levenshtein_matrix(x=sequences, y=sequences)

    assert dist_matrix[0, 0] == 0
    assert dist_matrix[0, 1] == clustering._levenshtein_distance(*sequences)
    np.testing.assert_array_almost_equal(dist_matrix.T, dist_matrix)


def test_clustering_create_model(population_no_args):
    clusters = clustering.PlanClusters(population_no_args)
    n_clusters = 2
    assert clusters.model is None
    clusters.fit(n_clusters=n_clusters)
    assert set(clusters.model.labels_) == set([0, 1])


def test_closest_matches_return_different_plan(population_no_args):
    clusters = clustering.PlanClusters(population_no_args)
    plan = population_no_args["chris"]["chris"].plan
    closest_plans = clusters.get_closest_matches(plan, 3)
    for closest_plan in closest_plans:
        assert plan != closest_plan


def test_closest_matches_are_ordered_by_distance(population_no_args):
    clusters = clustering.PlanClusters(population_no_args)
    plan = population_no_args["chris"]["chris"].plan
    encode = clusters.plans_encoder.plan_encoder.encode
    plan_encoded = encode(plan)
    closest_plans = clusters.get_closest_matches(plan, 3)
    dist = 1
    for closest_plan in closest_plans[::-1]:
        dist_match = clustering._levenshtein_distance(plan_encoded, encode(closest_plan))
        assert dist_match <= dist
        dist = dist_match


def test_cluster_plans_match_cluster_sizes(clusters):
    cluster_sizes = clusters.get_cluster_sizes()
    for cluster, size in cluster_sizes.items():
        assert len(clusters.get_cluster_plans(cluster)) == size
    assert cluster_sizes.sum() == len(clusters.plans)


def test_cluster_membership_includes_everyone(clusters, population_no_args):
    membership = clusters.get_cluster_membership()
    assert len(membership) == len(population_no_args)


def test_clustering_plot_calls_function(clusters, mocker):
    mocker.patch.object(clustering, "plot_activity_breakdown_area")
    clusters.plot_plan_breakdowns()
    clustering.plot_activity_breakdown_area.assert_called_once()

    mocker.patch.object(clustering, "plot_activity_breakdown_area_tiles")
    clusters.plot_plan_breakdowns_tiles()
    clustering.plot_activity_breakdown_area_tiles.assert_called_once()


def test_clustering_method_calls_correct_model(clusters, mocker):
    mocker.patch.object(clustering, "AgglomerativeClustering")
    clusters.fit(n_clusters=2, clustering_method="agglomerative")
    clustering.AgglomerativeClustering.assert_called_once()

    mocker.patch.object(clustering, "SpectralClustering")
    clusters.fit(n_clusters=2, clustering_method="spectral")
    clustering.SpectralClustering.assert_called_once()

    with pytest.raises(ValueError):
        clusters.fit(n_clusters=2, clustering_method="invalid_method")


def test_clustering_method_uses_correct_metric_matrix(clusters):
    clusters.fit(n_clusters=2, clustering_method="agglomerative")
    clusters.model.metric_matrix_ = clusters.distances

    # spectral clustering uses similarity instead of distnace
    clusters.fit(n_clusters=2, clustering_method="spectral")
    clusters.model.metric_matrix_ = 1 - clusters.distances
