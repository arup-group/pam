from __future__ import annotations

import itertools
from functools import lru_cache, partial
from multiprocessing import Pool
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from pam.core import Population

import numpy as np
import pandas as pd
from Levenshtein import ratio
from sklearn.cluster import AgglomerativeClustering, SpectralClustering

from pam.activity import Plan
from pam.planner.encoder import PlansCharacterEncoder
from pam.plot.plans import plot_activity_breakdown_area, plot_activity_breakdown_area_tiles


def _levenshtein_distance(a: str, b: str) -> float:
    """Levenstein distance between two strings."""
    return 1 - ratio(a, b)


def calc_levenshtein_matrix(x: list[str], y: list[str], n_cores=1) -> np.array:
    """Create a levenshtein distance matrix from two lists of strings."""
    levenshtein_distance = np.vectorize(_levenshtein_distance)
    if n_cores == 1:
        distances = levenshtein_distance(np.array(x).reshape(-1, 1), np.array(y))
    else:
        xs = np.array_split(x, n_cores)
        xs = [x.reshape(-1, 1) for x in xs]
        calc_levenshtein_matrix_partial = partial(levenshtein_distance, b=y)
        with Pool(n_cores) as p:
            distances = np.concatenate(p.map(calc_levenshtein_matrix_partial, xs))

    return distances


class PlanClusters:
    """Groups activity plans into clusters.
    Plan similarity is defined using the edit distance
        of character-encoded plan sequences.
    """

    def __init__(self, population: Population, n_cores: int = 1) -> None:
        self.population = population
        self.plans = list(population.plans())
        self.n_cores = n_cores
        self._distances = None
        self.model = None

        # encodings
        self.activity_classes = sorted(list(population.activity_classes) + ["travel"])
        self.plans_encoder = PlansCharacterEncoder(activity_classes=self.activity_classes)

    @property
    @lru_cache()
    def plans_encoded(self) -> list[str]:
        return self.plans_encoder.encode(self.plans)

    @property
    def distances(self) -> np.array:
        """Levenshtein distances between activity plans."""
        if self._distances is None:
            self._distances = calc_levenshtein_matrix(
                self.plans_encoded, self.plans_encoded, n_cores=self.n_cores
            )
        return self._distances

    @property
    def distances_no_diagonal(self) -> np.array:
        dist = self.distances.copy()
        np.fill_diagonal(dist, 1)
        return dist

    def fit(
        self,
        n_clusters: int,
        clustering_method: Literal["agglomerative", "spectral"] = "agglomerative",
        linkage: Optional[str] = "complete",
    ) -> None:
        """Fit an agglomerative clustering model.

        Args:
          n_clusters (int): The number of clusters to use.
          clustering_method (Literal['agglomerative', 'spectral']): The clustering method to use. Defaults to "agglomerative".
          linkage (str, optional): Linkage criterion. Defaults to "complete".

        """
        if clustering_method == "agglomerative":
            model = AgglomerativeClustering(
                n_clusters=n_clusters, linkage=linkage, metric="precomputed"
            )
            model.fit((self.distances))
        elif clustering_method == "spectral":
            model = SpectralClustering(n_clusters=n_clusters, affinity="precomputed")
            model.fit((1 - self.distances))
        else:
            raise ValueError(
                "Please select a valid clustering_method ('agglomerative' or 'spectral')"
            )

        self.model = model

    def get_closest_matches(self, plan, n) -> list[Plan]:
        """Get the n closest matches of a PAM activity schedule."""
        idx = self.plans.index(plan)
        idx_closest = np.argsort(self.distances_no_diagonal[idx])[:n]
        return [self.plans[x] for x in idx_closest]

    def get_cluster_plans(self, cluster: int) -> list:
        """Get the plans that belong in a specific cluster.

        Args:
            cluster (int): The cluster index.
        """
        return list(itertools.compress(self.plans, self.model.labels_ == cluster))

    def get_cluster_sizes(self) -> pd.Series:
        """Get the number of plans in each cluster."""
        return pd.Series(self.model.labels_).value_counts()

    def get_cluster_membership(self) -> dict:
        """Get the cluster membership of each person in the population.
        Returns a dictionary where the index values are (hid, pid) tuples,
            and the values are the correponding agents' clusters.
        """
        ids = [(hid, pid) for hid, pid, person in self.population.people()]
        return dict(zip(ids, self.model.labels_))

    def plot_plan_breakdowns(
        self, ax=None, cluster=None, activity_classes: Optional[list[str]] = None, **kwargs
    ):
        """Area plot of the breakdown of activities taking place every minute
        for a specific cluster.
        """
        if cluster is not None:
            plans = self.get_cluster_plans(cluster)
        else:
            plans = self.plans

        if activity_classes is None:
            activity_classes = self.activity_classes

        return plot_activity_breakdown_area(
            plans=plans, activity_classes=self.activity_classes, ax=ax, **kwargs
        )

    def plot_plan_breakdowns_tiles(self, n: Optional[int] = None, **kwargs):
        """Tiled area plot of the breakdown of activities taking place every minute,
        for the clusters with the top n number of plans.
        """
        if n is None:
            n = len(set(self.model.labels_))

        clusters = self.get_cluster_sizes().head(n).index
        plans = {cluster: self.get_cluster_plans(cluster) for cluster in clusters}

        return plot_activity_breakdown_area_tiles(
            plans=plans, activity_classes=self.activity_classes, **kwargs
        )
