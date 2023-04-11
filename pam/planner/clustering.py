from Levenshtein import ratio, hamming
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from typing import List, Optional
from pam.core import Population, Household, Person
from pam.activity import Plan
import pandas as pd
from functools import lru_cache, cached_property
from pam.planner.encoder import PlansCharacterEncoder
from pam.plot.plans import plot_activity_breakdown_area, plot_activity_breakdown_area_tiles
import itertools
from datetime import timedelta as td


def _levenshtein_distance(a: str, b: str) -> float:
    """
    Levenstein distance between two strings.
    """
    return 1 - ratio(a, b)


def calc_levenshtein_matrix(x: List[str], y: List[str]) -> np.array:
    """
    Create a levenshtein distance matrix from two lists of strings
    """
    levenshtein_distance = np.vectorize(_levenshtein_distance)
    distances = levenshtein_distance(np.array(x).reshape(-1, 1), np.array(y))
    return distances


class PlanClusters:
    def __init__(
        self,
        population: Population
    ) -> None:
        self.population = population
        self.plans = list(population.plans())
        self.model = None

        # encodings
        self.activity_classes = sorted(
            list(population.activity_classes) + ['travel']
        )
        self.plan_encoder = PlansCharacterEncoder(
            activity_classes=self.activity_classes)

    @cached_property
    def plans_encoded(self) -> List[str]:
        return self.plan_encoder.encode(self.plans)

    @cached_property
    def distances(self) -> np.array:
        """
        Levenshtein distances between activity plans
        """
        dist = calc_levenshtein_matrix(
            self.plans_encoded, self.plans_encoded)
        return dist

    @cached_property
    def distances_no_diagonal(self) -> np.array:
        dist = self.distances.copy()
        np.fill_diagonal(dist, 1)
        return dist

    def fit(
            self,
            n_clusters: int,
            linkage: str = 'complete',
    ) -> None:
        """
        :param n_clusters: The number of clusters to use.
        :param linkage: Linkage criterion
        """
        model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage,
            metric='precomputed'
        )
        model.fit((self.distances))

        self.model = model

    def get_closest_matches(self, plan, n) -> List[Plan]:
        """
        Get the n closest matches of a PAM activity schedule.
        """
        idx = self.plans.index(plan)
        idx_closest = np.argsort(self.distances_no_diagonal[idx])[:n]
        return [self.plans[x] for x in idx_closest]

    def get_cluster_plans(self, cluster: int):
        """
        Get the plans that belong in a specific cluster.

        :param cluster: The cluster index.
        """
        return list(
            itertools.compress(self.plans, self.model.labels_ == cluster)
        )

    def get_cluster_sizes(self) -> pd.Series:
        """
        Get the number of plans in each cluster.
        """
        return pd.Series(self.model.labels_).value_counts()
    
    def get_cluster_membership(self) -> dict:
        """
        Get the cluster membership of each person in the population.
        Returns a dictionary where the index values are (hid, pid) tuples,
            and the values are the correponding agents' clusters.
        """
        ids = [(hid, pid) for hid, pid, person in self.population.people()]
        return dict(zip(ids, self.model.labels_))

    def plot_plan_breakdowns(self, ax=None, cluster=None, **kwargs):
        """
        Area plot of the breakdown of activities taking place every minute
            for a specific cluster.
        """
        if cluster is not None:
            plans = self.get_cluster_plans(cluster)
        else:
            plans = self.plans

        return plot_activity_breakdown_area(
            plans=plans,
            activity_classes=self.activity_classes,
            ax=ax,
            **kwargs
        )

    def plot_plan_breakdowns_tiles(self, n: Optional[int] = None):
        """
        Tiled area plot of the breakdown of activities taking place every minute,
            for the clusters with the top n number of plans.
        """
        if n is None:
            n = len(set(self.model.labels_))

        clusters = self.get_cluster_sizes().head(n).index
        plans = {
            cluster: self.get_cluster_plans(cluster) for cluster in clusters
        }

        return plot_activity_breakdown_area_tiles(
            plans=plans,
            activity_classes=self.activity_classes
        )
