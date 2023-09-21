import random
import warnings
from typing import Any, Dict, Iterable, List, Optional, Union

import geopandas as gp
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.spatial import distance_matrix
from shapely.geometry import Point

from pam.activity import Activity, Leg
from pam.samplers.facility import FacilitySampler
from pam.utils import minutes_to_datetime as mtdt
from pam.variables import END_OF_DAY, EXPECTED_EUCLIDEAN_SPEEDS


def create_density_gdf(
    facility_zone: gp.GeoDataFrame,
    zone: gp.GeoDataFrame,
    activity: list[str],
    normalise: Optional[str] = None,
) -> gp.GeoDataFrame:
    """Calculate the spatial density of input activity.

    Args:
        facility_zone (gp.GeoDataFrame): Spatial join between facility and zone information.
        zone (gp.GeoDataFrame): zones information.
        activity (list[str]): a list of activities that are within facility data.
        normalise (Optional[str], optional): If given, normalise density against this variable. Defaults to None.

    Returns:
        gp.GeoDataFrame: measure of density of activities in each zone
    """
    if normalise is not None:
        density = (
            facility_zone.groupby([facility_zone.index, "activity", normalise])
            .agg({"id": "count"})
            .reset_index()
        )
        density.set_index(facility_zone.index.name, inplace=True)
        density = density[density["activity"].isin(activity)]
        density["density"] = density["id"] / density[normalise]
        total_density = density[~(density[normalise] == 0)]["density"].sum()
        density["density"] = density["density"] / total_density
    else:
        density = (
            facility_zone.groupby([facility_zone.index, "activity"])
            .agg({"id": "count"})
            .reset_index()
        )
        density.set_index(facility_zone.index.name, inplace=True)
        density = density[density["activity"].isin(activity)]
        density["density"] = density["id"] / density["id"].sum()

    # Convert back to geodataframe for merging.
    density = pd.merge(
        density, zone["geometry"], left_on=density.index, right_on=zone.index, how="left"
    )
    density.rename(columns={"key_0": facility_zone.index.name}, inplace=True)
    density = gp.GeoDataFrame(data=density, geometry="geometry")
    density.set_index(facility_zone.index.name, inplace=True)

    if np.isinf(density["density"]).sum() >= 1:
        warnings.warn("Your density gdf has infinite values")

    return density


class PivotDistributionSampler:
    """Defines a distribution, a sampler, and plots based on input values. The resulting distribution can be sampled
    for inputs required to build an agent plan (i.e, time of day, repetition of activities).
    """

    def __init__(self, bins: Iterable, pivots: dict, total=None):
        """Builds a dict distribution based on bins (i.e, hours) and pivots (i.e, hourly demand).

        Where the input pivot does not specify a value, values are estimated within the bin range by interpolation.

        Args:
            bins (Iterable): a range or dictionary of values
            pivots (dict): a dictionary of values associated with the bins.
            total (optional): Defaults to None.
        """
        self.demand = {}

        if bins[0] not in pivots:
            pivots[bins[0]] = 0
        if bins[-1] + 1 not in pivots:
            pivots[bins[-1] + 1] = 0

        pivot_keys = sorted(pivots.keys())

        for k in range(len(pivot_keys) - 1):
            ka = pivot_keys[k]
            kb = pivot_keys[k + 1]
            pivot_a = pivots[ka]
            pivot_b = pivots[kb]
            for i in bins:
                if ka <= i < kb:
                    self.demand[i] = self._interpolate(i, ka, pivot_a, kb, pivot_b)
                else:
                    continue

        if total is not None:
            dist_sum = sum(self.demand.values())
            for i in bins:
                self.demand[i] = (self.demand[i] / dist_sum) * total

    @staticmethod
    def _interpolate(i, ai, a, bi, b):
        "input values to build distribution between values a and ai."
        return a + (i - ai) * (b - a) / (bi - ai)

    def plot(self, plot_title, x_label, y_label):
        """Plots distribution to validate the distribution aligns with expected hourly demand."""
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(list(self.demand.keys()), list(self.demand.values()))
        ax.plot(list(self.demand.keys()), list(self.demand.values()), c="orange")
        ax.set_title(plot_title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        return fig

    def sample(self):
        return random.choices(list(self.demand.keys()), list(self.demand.values()), k=1)[0]


class FrequencySampler:
    """Object for initiating and sampling from frequency weighted distributing.
    This object includes three samplers: a single sample, multiple samples, or sample based on a threshold value
    (requires a threshold matrix).
    """

    def __init__(
        self,
        dist: Union[Iterable, pd.DataFrame],
        freq: Optional[Union[str, Iterable]] = None,
        threshold_matrix: Optional[pd.DataFrame] = None,
        threshold_value: Optional[Union[int, float]] = None,
    ) -> None:
        """

        Args:
            dist (Union[Iterable, pd.DataFrame]):
                Input distribution. If a DataFrame is given, the index will be used.
            freq (Optional[Union[str, Iterable]], optional):
                If given, weighting for input items, either as an iterable or a reference to a column of `dist` (which then must be a DataFrame).
                Defaults to None.
            threshold_matrix (Optional[pd.DataFrame], optional):
                A dataframe that will be reduced based on a specified threshold_value. Defaults to None.
            threshold_value (Optional[Union[int, float]], optional):
                A value to filter the threshold_matrix. This is the maximum allowed value. Defaults to None.
        """
        self.distribution = dist
        self.frequency = freq
        self.threshold_matrix = threshold_matrix
        self.threshold_value = threshold_value

    def sample(self) -> Any:
        """

        Returns:
            Any: Single object sampled from distribution

        """
        return random.choices(self.distribution, weights=self.frequency, k=1)[0]

    def samples(self, n: int = 1) -> list:
        """

        Args:
          n (int, optional): number of samples to be returned. Defaults to 1.

        Returns:
          list: objects sampled from distribution

        """
        return random.choices(self.distribution, weights=self.frequency, k=n)

    def threshold_sample(self):
        """Returns a sampler of a distribution that has been reduced based on a threshold value."""
        d_list = self.threshold_matrix
        d_list = d_list[d_list <= self.threshold_value].index
        d_threshold = self.distribution[self.distribution.index.isin(d_list)]

        if len(d_threshold) == 0:
            warnings.warn("No destinations within this threshold value, change threshold")
            return None
        else:
            return random.choices(
                list(d_threshold.index), weights=list(d_threshold[self.frequency]), k=1
            )[0]


def model_distance(o, d, scale=1.4):
    """Models distance between two shapely points."""
    return o.distance(d) * scale


def model_journey_time(
    distance: Union[float, int], speed: float = EXPECTED_EUCLIDEAN_SPEEDS["freight"]
) -> float:
    """

    Args:
        distance (Union[float, int]): Distance in metres.
        speed (float, optional): Speed in metres/second. Defaults to 50000 / 3600 (50km/hr).

    Returns:
        float: Modelled journey time.

    """
    return distance / speed


def model_activity_time(time: int, maxi: int = 3600, mini: int = 600) -> int:
    """Returns a duration that is between the minimum amount of seconds, an input journey time, or maximum time.

    Args:
        time (int): Time in seconds.
        maxi (int, optional): maximum time for a journey. Defaults to 3600.
        mini (int, optional): minimum time for a journey. Defaults to 600.

    Returns:
        int: maximum value between minimum time or the minimum of journey time and maximum time.

    """
    return max([mini, min([time, maxi])])


class TourPlanner:
    """Object for agents to efficiently plan their tours by sequencing stops and adding activities and legs.

    The TourPlanner optimises the sequence of stops using a Greedy Travelling Salesman Problem (TSP) algorithm based on Eucledian distances between sampled stops.
    It takes into account origin and destination zones, facility distributions, and other relevant parameters to build a tour plan for agents.
    """

    def __init__(
        self,
        stops: int,
        hour: int,
        minute: int,
        o_zone: str,
        d_dist: pd.DataFrame,
        d_freq: Union[str, Iterable],
        facility_sampler: FacilitySampler,
        activity_params: dict[str, str],
        threshold_matrix=None,
        threshold_value=None,
    ):
        """
        Args:
            stops (int): # of stops.
            hour (int): input of sampled hour.
            minute (int): input of sampled minute.
            o_zone (str): origin zone.
            d_dist (Union[Iterable, pd.DataFrame]): distribution of destination zones.
            d_freq (Union[str, Iterable]): frequency value to sample of destination distribution.
            facility_sampler (FacilitySampler):
            activity_params (dict[str, str]): dictionary of str of origin activity (str) and destination activity (str).
            threshold_matrix (optional): dataframe that will be reduced based on threshold value. Defaults to None.
            threshold_value (optional): maximum threshold value allowed between origin and destination in threshold_matrix. Defaults to None.
        """
        self.stops = stops
        self.hour = hour
        self.minute = minute
        self.o_zone = o_zone
        self.threshold_matrix = threshold_matrix
        self.d_dist = d_dist
        self.d_freq = d_freq
        self.threshold_value = threshold_value
        self.facility_sampler = facility_sampler
        self.o_activity = activity_params["o_activity"]
        self.d_activity = activity_params["d_activity"]

    def d_zone_sample_choice(self) -> str:
        """Samples a destination zone (d_zone) as a string, dependent on the presence of a threshold matrix.

        Returns:
            str: d_zone

        """ ""
        if self.threshold_matrix is None:
            d_zone = FrequencySampler(self.d_dist.index, self.d_dist[self.d_freq]).sample()
        else:
            d_zone = FrequencySampler(
                dist=self.d_dist,
                freq=self.d_freq,
                threshold_matrix=self.threshold_matrix.loc[self.o_zone],
                threshold_value=self.threshold_value,
            ).threshold_sample()

        return d_zone

    def sample_destinations(self, o_loc) -> List[Dict[str, Any]]:
        """Samples destinations and prevents repeated sampling of destinations, and prevents origin from be sampled as a destination

        Args:
            o_loc (Point): shapely.geometry.Point representing the sampled origin location.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing information about each stop in the tour.
        """
        d_seq = []
        sampled_d_facilities = []

        for stop in range(self.stops):
            # If threshold matrix is none, sample a random d_zone, else select a d_zone within threshold value
            d_zone = TourPlanner.d_zone_sample_choice(self)
            # once d_zone is selected, select a specific point location for d_activity
            d_facility = self.facility_sampler.sample(d_zone, self.d_activity)

            # prevent the depot from being sampled as a delivery (destination) or duplicate sampling of delivery (destination) locations
            while d_facility == o_loc or d_facility in sampled_d_facilities:
                d_zone = TourPlanner.d_zone_sample_choice(self)
                d_facility = self.facility_sampler.sample(d_zone, self.d_activity)

            # append select d_facility to sampled list for tracking
            sampled_d_facilities.append(d_facility)

            # append to a dictionary to sequence destinations
            d_seq.append(
                {
                    "stops": stop,
                    "destination_zone": d_zone,
                    "destination_facility": d_facility,
                    "distance": model_distance(o_loc, d_facility),
                }
            )
        return d_seq

    def create_distance_matrix(self, o_loc: Point, d_seq: list) -> np.ndarray:
        """Create a distance matrix between the origin location and a list of destinations.

        Args:
            o_loc (Point): shapely.geometry.Point representing the sampled origin location.
            d_seq (List[Dict[str, Any]]): A list of dictionaries containing information about each stop in the tour.

        Returns:
            np.ndarray: 2D NumPy array representing the distance matrix between origin and destinations.
        """
        # extract o_loc coordinates into array
        o_location = np.array([[o_loc.x, o_loc.y]])

        # extract d_facility
        d_locations = np.array(
            [[location.x, location.y] for location in [d["destination_facility"] for d in d_seq]]
        )

        locs = np.concatenate([o_location, d_locations], 0)
        dist_matrix = distance_matrix(locs, locs)

        return dist_matrix

    def approx_greedy_tsp(self, dist_matrix) -> List[int]:
        """Approximate solution to the Travelling Saleman Problem using the GreedyTSP algorithm.

        Args:
            dist_matrix (np.ndarray): 2D NumPy array representing the distance matrix between origin and destinations.

        Returns:
            List[int]: List of integers representing the optimised sequence of stops.
        """
        distance_graph = nx.from_numpy_array(dist_matrix)
        seq = nx.algorithms.approximation.greedy_tsp(distance_graph, source=0)

        return seq

    def reorder_destinations(self, d_seq, seq) -> List[Dict[str, Any]]:
        """Reorder the destinations based on the provided sequence.

        Args:
            d_seq (List[Dict[str, Any]]): A list of dictionaries containing information about each stop (destination) in the tour.
            seq (List[int]): List of integers representing the optimised sequence of stops.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the reordered stops (destinations)
        """
        # use `seq` to re-order `d_locs` into an ordered list of dictionaries
        # remove o_loc (first and last stop) from sequence & adjust sequence range
        d_seq = [d_seq[order - 1] for order in seq[1:-1]]

        return d_seq

    def sequence_stops(self) -> tuple[Point, list[Point], list[Point]]:
        """Creates a sequence for a number of stops. Sequence is determined by approximated greedy TSP

        Returns:
          tuple[Point, list, list]: (o_loc, d_zones, d_locs).

        """
        o_loc = self.facility_sampler.sample(self.o_zone, self.o_activity)

        d_seq = TourPlanner.sample_destinations(self, o_loc)
        dist_matrix = TourPlanner.create_distance_matrix(self, o_loc, d_seq)

        seq = TourPlanner.approx_greedy_tsp(self, dist_matrix)

        d_optimised_seq = TourPlanner.reorder_destinations(self, d_seq, seq)

        # sort distance: furthest facility to closest facility to origin facility. The final stop should be closest to origin.
        d_zones = [item.get("destination_zone") for item in d_optimised_seq]
        d_locs = [item.get("destination_facility") for item in d_optimised_seq]

        return o_loc, d_zones, d_locs

    def add_tour_activity(
        self, agent: str, k: Iterable, zone: str, loc: Point, activity_type: str, time_params: dict
    ) -> int:
        """Add activity to tour plan. This will add an activity to the agent plan after each leg within the tour.

        Args:
          agent (str): agent for which the activity will be added to Plan
          k (int): when used in a for loop, k populates the next sequence value
          zone (str): zone where activity takes place
          loc (shapely.Point): facility location where activity takes place
          activity_type (str): this function has specific logic for 'return_origin'
          time_params (dict[str, str]): dictionary of time_params that may be time samplers or times of previous journeys

        Returns:
          int: end_tm of activity.

        """
        if activity_type == self.o_activity:
            start_tm = 0
            end_tm = (time_params["hour"] * 60) + time_params["minute"]
            seq = 1
            act = activity_type
        elif activity_type == "return_origin":
            start_tm = time_params["start_tm"]  # end_tm
            end_tm = time_params["end_tm"]  # END_OF_DAY we'll let pam trim this to 24 hours later
            seq = k + 2
            act = self.o_activity
        else:
            start_tm = time_params["end_tm"]
            end_tm = time_params["end_tm"] + int(time_params["stop_duration"] / 60)
            seq = k + 2
            act = activity_type

        # Activity plan requires mtdt format, but int format needs to passed for other functions to calculate new start time.
        # END_OF_DAY is already in mtdt format, adding an exception to keep set mtdt format when not END_OF_DAY.
        if end_tm is not END_OF_DAY:
            end_tm_mtdt = mtdt(end_tm)
        else:
            end_tm_mtdt = end_tm

        agent.add(
            Activity(
                seq=seq,
                act=act,
                area=zone,
                loc=loc,
                start_time=mtdt(start_tm),
                end_time=end_tm_mtdt,
            )
        )

        return end_tm

    def add_tour_leg(
        self,
        agent: str,
        k: Iterable,
        o_zone: str,
        o_loc: Point,
        d_zone: str,
        d_loc: Point,
        start_tm: int,
        end_tm: int,
    ) -> int:
        """Leg to Next Activity within the tour. This adds a leg to the agent plan after each activity is complete within the tour.
        Args:
          agent (str): agent for which the leg will be added to Plan
          k (Iterable): when used in a for loop, k populates the next sequence value
          o_zone (str): origin zone of leg
          o_loc (shapely.point): origin facility of leg
          d_zone (str): destination zone of leg
          d_loc (shapely.point): destination facility of leg
          start_tm (int): obtained from DurationEstimator object
          end_tm (int): obtained from DurationEstimator object

        Returns:
          int: new end_tm after leg is added to plan.
        """
        agent.add(
            Leg(
                seq=k + 1,
                mode="car",
                start_area=o_zone,
                end_area=d_zone,
                start_loc=o_loc,
                end_loc=d_loc,
                start_time=mtdt(start_tm),
                end_time=mtdt(end_tm),
            )
        )

        return end_tm

    def apply(self, agent: str, o_loc: Point, d_zones: list, d_locs: list) -> None:
        """Apply the above functions to the agent to build a plan.
        1. Add first activity
        2. cycle through d_plan and add leg/activity
        3. add leg/activity to return to origin

        Args:
          agent (str): agent to build a plan fory
          o_loc (shapely.Point): origin facility of leg & activity
          d_zones (list): destination zones of leg & activity
          d_locs (list): destination facilities of leg & activity.
        """

        # add origin activity
        time_params = {"hour": self.hour, "minute": self.minute}
        # first activity
        end_tm = self.add_tour_activity(
            agent=agent,
            k=1,
            zone=self.o_zone,
            loc=o_loc,
            activity_type=self.o_activity,
            time_params=time_params,
        )
        # add stops to plan
        for k in range(len(d_locs)):
            if k == 0:
                previous_zone = self.o_zone
                previous_loc = o_loc
            else:
                previous_zone = d_zones[k - 1]
                previous_loc = d_locs[k - 1]

            start_tm = end_tm
            trip_distance = model_distance(previous_loc, d_locs[k])
            trip_duration = model_journey_time(trip_distance)
            activity_duration = model_activity_time(trip_duration)
            end_tm = end_tm + int(trip_duration / 60)

            end_tm = self.add_tour_leg(
                agent=agent,
                k=k,
                o_zone=previous_zone,
                o_loc=previous_loc,
                d_zone=d_zones[k],
                d_loc=d_locs[k],
                start_tm=start_tm,
                end_tm=end_tm,
            )

            time_params = {"end_tm": end_tm, "stop_duration": activity_duration}
            end_tm = self.add_tour_activity(
                agent=agent,
                k=k,
                zone=d_zones[k],
                loc=d_locs[k],
                activity_type=self.d_activity,
                time_params=time_params,
            )
        # returning to origin

        start_tm = end_tm
        trip_distance = model_distance(d_locs[len(d_locs) - 1], o_loc)
        trip_duration = model_journey_time(trip_distance)
        end_tm = end_tm + int(trip_duration / 60)

        end_tm = self.add_tour_leg(
            agent=agent,
            k=k + 1,
            o_zone=d_zones[-1],
            o_loc=d_locs[-1],
            d_zone=self.o_zone,
            d_loc=o_loc,
            start_tm=start_tm,
            end_tm=end_tm,
        )

        time_params = {"start_tm": end_tm, "end_tm": END_OF_DAY}
        end_tm = self.add_tour_activity(
            agent=agent,
            k=k,
            zone=self.o_zone,
            loc=o_loc,
            activity_type="return_origin",
            time_params=time_params,
        )


class ValidateTourOD:
    """Object to build a dataframe that produces both spatial and statistical plots to validate the tour origin and
    destinations align with input data.
    """

    def __init__(
        self,
        trips: pd.DataFrame,
        zone: gp.GeoDataFrame,
        o_dist: pd.DataFrame,
        d_dist: pd.DataFrame,
        o_activity: str,
        d_activity: str,
        o_freq: str,
        d_freq: str,
    ):
        """Create a dataframe that counts the number of origin and destination activities.

        Merge this against the density information from the input origin and destination samplers.

        Args:
            trips (pd.DataFrame): the legs.csv output after building population.
            zone (gp.GeoDataFrame):
            o_dist (pd.DataFrame): sampler containing origin distributions to be sampled.
            d_dist (pd.DataFrame): sampler containing destination distributions to be sampled.
            o_activity (str): activity utilised within o_dist.
            d_activity (str): activity utilised within d_dist.
            o_freq (str): destination frequency that is used to sample origin distributions.
            d_freq (str): destination frequency that is used to sample destination distributions.
        """
        # Create a dataframe to plot od trips and compare against facility density and flows density.
        df_trips_o = (
            trips[trips["origin activity"] == o_activity]
            .groupby(["ozone"])
            .agg({"pid": "count"})
            .reset_index()
        )
        df_trips_o.rename(columns={"pid": "origin_trips"}, inplace=True)
        df_trips_o.set_index("ozone", inplace=True)

        df_trips_d = (
            trips[trips["destination activity"] == d_activity]
            .groupby(["dzone"])
            .agg({"pid": "count"})
            .reset_index()
        )
        df_trips_d.rename(columns={"pid": "destination_trips"}, inplace=True)
        df_trips_d.set_index("dzone", inplace=True)

        self.od_density = zone.copy()

        # Merge in trips information
        self.od_density = pd.merge(
            self.od_density,
            df_trips_o,
            left_on=self.od_density.index,
            right_on=df_trips_o.index,
            how="left",
        )
        self.od_density = pd.merge(
            self.od_density, df_trips_d, left_on="key_0", right_on=df_trips_d.index, how="left"
        )

        # Merge in density information
        o_density = o_dist.reset_index()
        o_density = o_density.groupby(o_dist.index).agg({o_freq: "sum"})
        d_density = d_dist.reset_index()
        d_density = d_density.groupby(d_dist.index).agg({d_freq: "sum"})

        self.od_density[f"{o_activity}_density"] = self.od_density.key_0.map(o_density[o_freq])
        self.od_density[f"{d_activity}_density"] = self.od_density.key_0.map(d_density[d_freq])

        self.od_density.rename(columns={"key_0": zone.index.name}, inplace=True)
        self.od_density.set_index(zone.index.name, inplace=True)

        # Add in features for analysis
        self.od_density = self.od_density.fillna(0)
        self.od_density["origin_trip_density"] = (
            self.od_density.origin_trips / self.od_density.origin_trips.sum()
        )
        self.od_density["destination_trip_density"] = (
            self.od_density.destination_trips / self.od_density.destination_trips.sum()
        )
        self.od_density["origin_diff"] = (
            self.od_density["origin_trip_density"] - self.od_density[f"{o_activity}_density"]
        )
        self.od_density["destination_diff"] = (
            self.od_density["destination_trip_density"] - self.od_density[f"{d_activity}_density"]
        )

    def plot_validate_spatial_density(
        self,
        title_1: str,
        title_2: str,
        density_metric: str,
        density_trips: str,
        cmap: str = "coolwarm",
    ) -> plt.Figure:
        """Creates a spatial plot between input densities and resulting trips to validate trips spatially align with input densities.

        Args:
          title_1 (str): Input densities plot title.
          title_2 (str): Resulting trips plot title.
          density_metric (str): the measure for density output from the above dataframe, in the format of 'activity_density'
          density_trips (str): the measure of trips that require validation, either 'origin_trips' or 'destination_trips'.
          cmap (str): Defaults to "coolwarm".

        Returns:
            plt.Figure:
        """
        fig, ax = plt.subplots(1, 2, figsize=(20, 10))

        self.od_density.plot(density_metric, ax=ax[0], cmap=cmap)
        ax[0].axis("off")
        ax[0].set_title(title_1)

        self.od_density.plot(density_trips, ax=ax[1], cmap=cmap)
        ax[1].axis("off")
        ax[1].set_title(title_2)

        im = plt.gca().get_children()[0]
        cax = fig.add_axes([1, 0.2, 0.03, 0.6])
        plt.colorbar(im, cax=cax)

        return fig

    def plot_compare_density(
        self, title_1: str, title_2: str, o_activity: str, d_activity: str
    ) -> plt.Figure:
        """Compares density of input origin/destination activities and trips. As density of locations increases, so should trips.

        Args:
          title_1 (str): input for plot origin title name.
          title_2 (str): input for plot destination title name.
          o_activity (str): activity used to measure density of origin locations.
          d_activity (str): activity used to measure density of destination locations.

        Returns:
            plt.Figure:
        """
        fig, ax = plt.subplots(1, 2, figsize=(15, 7))

        m1, b1 = np.polyfit(self.od_density[o_activity], self.od_density.origin_trip_density, 1)
        m2, b2 = np.polyfit(
            self.od_density[d_activity], self.od_density.destination_trip_density, 1
        )

        ax[0].scatter(x=o_activity, y="origin_trip_density", data=self.od_density)
        ax[0].plot(
            self.od_density[o_activity],
            (m1 * self.od_density[o_activity] + b1),
            label="y = {:.2f} + {:.2f}*x".format(m1, b1),
        )
        ax[0].legend(loc="lower right")
        ax[0].set_title(title_1)

        ax[1].scatter(x=d_activity, y="destination_trip_density", data=self.od_density)
        ax[1].plot(
            self.od_density[o_activity],
            (m2 * self.od_density[o_activity] + b2),
            label="y = {:.2f} + {:.2f}*x".format(m2, b2),
        )
        ax[1].legend(loc="lower right")
        ax[1].set_title(title_2)

        return fig

    def plot_density_difference(
        self, title_1: str, title_2: str, cmap: str = "coolwarm"
    ) -> plt.Figure:
        """Creates a spatial plot of the difference between input and output densities.

        Args:
          title_1 (str): input for plot origin title name.
          title_2 (str): input for plot destination title name.
          cmap (str, optional): Defaults to "coolwarm"

        Returns:
            plt.Figure:
        """
        fig, ax = plt.subplots(1, 2, figsize=(20, 10))

        self.od_density.plot("origin_diff", ax=ax[0], cmap=cmap)
        ax[0].axis("off")
        ax[0].set_title(title_1)

        self.od_density.plot("destination_diff", ax=ax[1], cmap=cmap)
        ax[1].axis("off")
        ax[1].set_title(title_2)

        im = plt.gca().get_children()[0]
        cax = fig.add_axes([1, 0.2, 0.03, 0.6])
        plt.colorbar(im, cax=cax)

        return fig
