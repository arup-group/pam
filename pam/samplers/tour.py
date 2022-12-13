import geopandas as gp
import matplotlib
from matplotlib import pyplot as plt
import random
import pandas as pd
import numpy as np
import warnings

import pam
from pam.activity import Activity, Leg
from pam.variables import END_OF_DAY
from pam.utils import minutes_to_datetime as mtdt

def interpolate(i, ai, a, bi, b):
    """
    :param i, ai, a, bi, b: input values to build distribution between values a and b
    """
    return a + (i-ai) * (b-a) / (bi-ai)

def create_density_gdf(facility_zone, zone, activity, normalise=None):
    """
    Returns a geodataframe that calculates the spatial density of input activity. The normalise flag
    allows for the user to decide what variable to normalise density against.
    :param facility_zone: a geodataframe that is the spatial join between facility and zone information
    :param zone: a geodataframe with zones information
    :param activity: a list of activities (in string format) that are within facility data
    :return: a geodataframe that measures the density of activities in each zone. 
    """
    
    if normalise is not None:
        density = facility_zone.groupby([facility_zone.index, 'activity', normalise]).agg({'id':'count'}).reset_index()    
        density.set_index(facility_zone.index.name, inplace=True)
        density = density[density['activity'].isin(activity)]
        density['density'] = density['id']/density[normalise]
        total_density = density[~(density[normalise]==0)]['density'].sum()
        density['density'] = density['density']/total_density
    else:
        density = facility_zone.groupby([facility_zone.index, 'activity']).agg({'id':'count'}).reset_index()    
        density.set_index(facility_zone.index.name, inplace=True)
        density = density[density['activity'].isin(activity)]
        density['density'] = density['id']/density['id'].sum()

    # Convert back to geodataframe for merging.
    density = pd.merge(density, zone['geometry'], left_on = density.index, right_on=zone.index, how='left')
    density.rename(columns={'key_0':facility_zone.index.name}, inplace=True)
    density = gp.GeoDataFrame(data=density, geometry='geometry')
    density.set_index(facility_zone.index.name, inplace=True)

    if np.isinf(density['density']).sum()>=1:
        warnings.warn('Your density gdf has infinite values')
    
    return density 


class PivotDistributionSampler: 
    """
    Defines a distribution, a sampler, and plots based on input values. The resulting distribution can be sampled
    for inputs required to build an agent plan (i.e, time of day, repetition of activities).
    """

    def __init__(self, bins, pivots, total=None):
        """
        Builds a dict distribution based on bins (i.e, hours) and pivots (i.e, hourly demand). 
        The interpolate function defined above is applied to estimate values within the bin range where the input pivot does not specify a value.
        :param bins: a range or dictionary of values
        :param pivots: a dictionary of values associated with the bins
        """

        self.demand = {}
    
        if bins[0] not in pivots:
            pivots[bins[0]] = 0
        if bins[-1]+1 not in pivots:
            pivots[bins[-1]+1] = 0
        
        pivot_keys = sorted(pivots.keys())
    
        for k in range(len(pivot_keys)-1):
            ka = pivot_keys[k]
            kb = pivot_keys[k+1]
            pivot_a = pivots[ka]
            pivot_b = pivots[kb]
            for i in bins:
                if ka <= i < kb:
                    self.demand[i] = interpolate(i, ka, pivot_a, kb, pivot_b)
                else:
                    continue       
        
        if total is not None:
            dist_sum = sum(self.demand.values())
            for i in bins:
                self.demand[i] = (self.demand[i]/dist_sum)*total

    def plot(self, plot_title, x_label, y_label):
        """
        Plots distribution to validate the distribution aligns with expected hourly demand.
        """

        fig, ax = plt.subplots(figsize=(10,4))
        ax.bar(list(self.demand.keys()), list(self.demand.values()))
        ax.plot(list(self.demand.keys()), list(self.demand.values()), c = 'orange')
        ax.set_title(plot_title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        return fig
    
    def sample(self):
        return random.choices(list(self.demand.keys()), list(self.demand.values()), k=1)[0]


class FrequencySampler: 
    """
    Object for initiating and sampling from frequency weighted distributing. 
    This object includes three samplers: a single sample, multiple samples, or sample based on a threshold value 
    (requires a threshold matrix).
    """
    def __init__(self, dist, freq=None, threshold_matrix=None, threshold_value=None):
        """
        :param dist: a dictionary of an input distribution
        :param freq: a parameter to weight the samplers
        :param threshold_matrix: a dataframe that will be reduced based on a specified threshold_value.
        :param threshold_value: a value to filter the threshold_matrix. This is the maximum allowed value.
        """

        self.distribution = dist
        self.frequency = freq
        self.threshold_matrix = threshold_matrix
        self.threshold_value = threshold_value
        
    def sample(self):
        """
        :return: single object or list of objects sampled from distribution
        """
        return random.choices(self.distribution, weights=self.frequency, k=1)[0]
    
    def samples(self, n=1):
        """
        :param n: number of samples to be returned
        :return: single object or list of objects sampled from distribution
        """
        return random.choices(self.distribution, weights=self.frequency, k=n)
    
    def threshold_sample(self):
        """
        Returns a sampler of a distribution that has been reduced based on a threshold value.
        """

        d_list = self.threshold_matrix
        d_list = d_list[d_list<=self.threshold_value].index
        d_threshold = self.distribution[self.distribution.index.isin(d_list)]
        
        if len(d_threshold) == 0:
            warnings.warn('No destinations within this threshold value, change threshold')
            return None
        else:
            return random.choices(list(d_threshold.index), weights=list(d_threshold[self.frequency]), k=1)[0]        
    

class ActivityDuration: 
    """
    Object to estimate the distance, journey time, and stop time of activities. 
    The last function activity_duration combines these three functions to output parameters that help build tour plans.
    """

    def model_distance(self, o, d, scale=1.4):
        """
        Models distance between two shapely points
        """
        return o.distance(d) * scale                                                                                                                 

    def model_journey_time(self, distance, speed=50000/3600):
        """
        :param distance: in m
        :param speed: in m/s, default 50km/hr
        :return: modelled journey time
        """
        return distance / speed

    def model_stop_time(self, time, maxi=3600, mini=600): 
        """
        Returns a duration that is between the minimum amount of seconds, an input journey time, or maximum time.
        :param time: in s
        :param maxi: maximum time for a journey
        :param mini: minimum time for a journey
        :return: maximum value between minimum time or the minimum of journey time and maximum time
        """
        return max([mini, min([time, maxi])])

    def model_activity_duration(self, o_loc, d_loc, end_tm, speed=50000/3600, maxi=3600, mini=600):
        """ 
        Returns estimated Activity Duration, which is combination of previous three functions to return parameters 
        for next activity in Plan.
        :param o_loc: origin facility
        :param d_loc: destination facility
        :param end_tm: most recent end time of previous leg
        :param speed: speed of vehicle, default at 50km/hr
        :param maxi: maximum stop time
        :param mini: minimum stop time
        :return: stop_duration, start_tm, and end_tm for new activity
        """

        trip_distance = self.model_distance(o_loc, d_loc)
        trip_duration = self.model_journey_time(trip_distance, speed)
        stop_duration = self.model_stop_time(trip_duration, maxi, mini)

        start_tm = end_tm
        end_tm = end_tm + int(trip_duration/60)

        return stop_duration, start_tm, end_tm


class TourPlanner:
    """
    Object to plan the tour of the agent. This includes sequencing the stops and adding the activity and leg via an apply method.
    """
    
    def __init__(self, stops, hour, minute, o_zone, d_dist, d_freq, facility_sampler, activity_params, threshold_matrix=None, threshold_value=None):
        """
        :params stops: # of stops
        :params hour: input of sampled hour
        :params minute: input of sampled minute
        :params o_zone: origin zone
        :params d_dist: distribution of destination zones
        :params d_freq: frequency value to sample of destination distribution
        :params facility_sampler: returned object from FacilitySampler
        :params activity_params: dictionary of str of origin activity (str) and destination activity (str)
        :params threshold_matrix: dataframe that will be reduced based on threshold value
        :params threshold_value: maximum threshold value allowed between origin and destination in threshold_matrix.
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
        self.o_activity = activity_params['o_activity']
        self.d_activity = activity_params['d_activity']

    def sequence_stops(self):
        """
        Creates a sequence for a number of stops. Sequence is determined by distance from origin. 
        :returns: o_loc, d_zones and d_locs (dataframe of sequenced destinations)

        TODO - Method to sequence stops with different logic (i.e, minimise distance between stops). 
        """

        o_loc = self.facility_sampler.sample(self.o_zone, self.o_activity)

        d_seq = []

        for j in range(self.stops):
            # If threshold matrix is none, sample a random d_zone, else select a d_zone within threshold value
            if self.threshold_matrix is None:
                d_zone = FrequencySampler(self.d_dist.index, self.d_dist[self.d_freq]).sample()
            else:
                d_zone = FrequencySampler(dist=self.d_dist,
                                          freq=self.d_freq,
                                          threshold_matrix=self.threshold_matrix.loc[self.o_zone],
                                          threshold_value = self.threshold_value
                                          ).threshold_sample()
            # once d_zone is selected, select a specific point location for d_activity                          
            d_facility = self.facility_sampler.sample(d_zone, self.d_activity)

            # append to a dictionary to sequence destinations
            d_seq.append({
                'stops': j,
                'destination_zone': d_zone,
                'destination_facility': d_facility,
                'distance': ActivityDuration().model_distance(o_loc, d_facility)
            })

        # sort distance: furthest facility to closest facility to origin facility. The final stop should be closest to origin.
        d_seq = sorted(d_seq, key=lambda item: item.get('distance'), reverse=True)
        d_zones = [item.get('destination_zone') for item in d_seq]
        d_locs = [item.get('destination_facility') for item in d_seq]

        return o_loc, d_zones, d_locs

    def add_tour_activity(self, agent, k, zone, loc, activity_type, time_params):
        """
        Add activity to tour plan.
        :params agent: agent for which the activity will be added to Plan
        :params k: when used in a for loop, k populates the next sequence value
        :params zone: zone where activity takes place
        :params loc: facility location where activity takes place
        :params activity_type: str, this function has specific logic for 'return_origin'
        :params time_params: dictionary of time_params that may be time samplers or times of previous journeys
        :return: end_tm of activity
        """

        if activity_type == self.o_activity:
            start_tm = 0
            end_tm = (time_params['hour']*60) + time_params['minute']
            seq = 1
            act = activity_type
        elif activity_type == 'return_origin':
            start_tm = time_params['start_tm'] # end_tm
            end_tm = time_params['end_tm']  # END_OF_DAY we'll let pam trim this to 24 hours later
            seq = k+2
            act = self.o_activity
        else:
            start_tm = time_params['end_tm']
            end_tm = time_params['end_tm'] + int(time_params['stop_duration']/60)
            seq = k+2
            act = activity_type
        
        # Activity plan requires mtdt format, but int format needs to passed for other functions to calculate new start time.
        # END_OF_DAY is already in mtdt format, adding an exception to keep set mtdt format when not END_OF_DAY.
        if end_tm is not END_OF_DAY:
            end_tm_mtdt = mtdt(end_tm)
        else:
            end_tm_mtdt=end_tm

        agent.add(Activity(
            seq=seq,
            act=act,
            area=zone,
            loc=loc,
            start_time=mtdt(start_tm),
            end_time=end_tm_mtdt
        ))

        return end_tm        

    def add_tour_leg(self, agent, k, o_zone, o_loc, d_zone, d_loc, start_tm, end_tm):
        """ 
        Leg to Next Delivery.
        :params agent: agent for which the leg will be added to Plan
        :params k: when used in a for loop, k populates the next sequence value
        :params o_zone: origin zone of leg
        :params o_loc: origin facility of leg
        :params d_zone: destination zone of leg
        :params d_loc: destination facility of leg
        :params start_tm, end_tm: obtained from ActivityDuration object
        :returns: new end_tm after leg is added to plan
        """

        agent.add(Leg(
            seq=k+1,
            mode='car', 
            start_area=o_zone,
            end_area=d_zone,
            start_loc=o_loc,
            end_loc=d_loc,
            start_time=mtdt(start_tm),
            end_time=mtdt(end_tm), 
        ))

        return end_tm

    def add_return_origin(self, agent, k, o_loc, d_zone, d_loc, end_tm):
        """ 
        Driver returns to origin, from their most recent stop to the origin location.
        :params agent: agent for which the leg & activity will be added to Plan
        :params k: when used in a for loop, k populates the next sequence valuey
        :params o_loc: origin facility of leg & activity
        :params d_zone: destination zone of leg & activity
        :params d_loc: destination facility of leg & activity
        :params end_tm: obtained from ActivityDuration object
        :params speed: default setting of 50km/hr
        :return: end_tm after returning to origin.
        """

        trip_distance = ActivityDuration().model_distance(o_loc, d_loc)
        trip_duration = ActivityDuration().model_journey_time(trip_distance)

        start_tm = end_tm
        end_tm = end_tm + int(trip_duration/60)

        end_tm = self.add_tour_leg(agent=agent, k=k, o_zone=d_zone, o_loc=d_loc, d_zone=self.o_zone, d_loc=o_loc, start_tm=start_tm, end_tm=end_tm)

        time_params = {'start_tm':end_tm, 'end_tm':END_OF_DAY}
        end_tm = self.add_tour_activity(agent=agent, k=k, zone=self.o_zone,loc=o_loc, activity_type='return_origin',time_params=time_params)

        return end_tm

    def apply(self, agent, o_loc, d_zones, d_locs):
        """
        Apply the above functions to the agent to build a plan. 
        :params agent: agent to build a plan fory
        :params o_loc: origin facility of leg & activity
        :params d_zones: destination zones of leg & activity
        :params d_locs: destination facilities of leg & activity
        """
        
        time_params = {'hour':self.hour, 'minute':self.minute}
        end_tm = self.add_tour_activity(agent=agent, k=1, zone=self.o_zone, loc=o_loc, activity_type=self.o_activity, time_params=time_params)

        for k in range(self.stops):
            stop_duration, start_tm, end_tm = ActivityDuration().model_activity_duration(o_loc, d_locs[k], end_tm)
            if (mtdt(end_tm) >= END_OF_DAY) | (mtdt(end_tm + int(stop_duration/60)) >= END_OF_DAY):
                break               
            elif k == 0:
                end_tm = self.add_tour_leg(agent=agent, k=k, o_zone=self.o_zone, o_loc=o_loc, d_zone=d_zones[k], d_loc=d_locs[k], start_tm=start_tm, end_tm=end_tm)

                time_params = {'end_tm':end_tm, 'stop_duration':stop_duration}
                end_tm = self.add_tour_activity(agent=agent, k=k, zone=d_zones[k], loc=d_locs[k], activity_type=self.d_activity, time_params=time_params)
            else: 
                end_tm = self.add_tour_leg(agent=agent, k=k, o_zone=d_zones[k-1], o_loc=d_locs[k-1], d_zone=d_zones[k], d_loc=d_locs[k], start_tm=start_tm, end_tm=end_tm)

                time_params = {'end_tm':end_tm, 'stop_duration':stop_duration}
                end_tm = self.add_tour_activity(agent=agent, k=k, zone=d_zones[k], loc=d_locs[k], activity_type=self.d_activity, time_params=time_params)
        
        end_tm = self.add_return_origin(agent=agent, k=self.stops, o_loc=o_loc, d_zone=d_zones[self.stops-1], d_loc=d_locs[self.stops-1], end_tm=end_tm)


class ValidateTourOD:
    """
    Object to build a dataframe that produces both spatial and statistical plots to validate the tour origin and 
    destinations align with input data.
    """

    def __init__(self, trips, zone, o_dist, d_dist, o_activity, d_activity, o_freq, d_freq):
        """
        Create a dataframe that counts the number of origin and destination activities. 
        Merge this against the density information from the input origin and destination samplers.
        :params trips: dataframe, the legs.csv output after building population
        :params zone: zones geodataframe
        :params o_dist, d_dist: samplers containing origin and destination distributions to be sampled.
        :params o_activity, d_activity: activities utilised within the o_dist and d_dist
        :params o_freq, d_freq: frequencies that are used to sample origin and destination distributions.
        """

        # Create a dataframe to plot od trips and compare against facility density and flows density.
        df_trips_o = trips[trips['origin activity']==o_activity].groupby(['ozone']).agg({'pid':'count'}).reset_index()
        df_trips_o.rename(columns={'pid':'origin_trips'}, inplace=True)
        df_trips_o.set_index('ozone', inplace=True)

        df_trips_d = trips[trips['destination activity']==d_activity].groupby(['dzone']).agg({'pid':'count'}).reset_index()
        df_trips_d.rename(columns={'pid':'destination_trips'}, inplace=True)
        df_trips_d.set_index('dzone', inplace=True)

        self.od_density = zone.copy()

        # Merge in trips information
        self.od_density = pd.merge(self.od_density, df_trips_o, left_on=self.od_density.index, right_on=df_trips_o.index, how='left')
        self.od_density = pd.merge(self.od_density, df_trips_d, left_on='key_0', right_on=df_trips_d.index, how='left')

        # Merge in density information
        o_density = o_dist.reset_index()
        o_density = o_density.groupby(o_dist.index).agg({o_freq:'sum'})
        d_density = d_dist.reset_index()
        d_density = d_density.groupby(d_dist.index).agg({d_freq:'sum'})

        self.od_density[f'{o_activity}_density'] = self.od_density.key_0.map(o_density[o_freq])
        self.od_density[f'{d_activity}_density'] = self.od_density.key_0.map(d_density[d_freq])

        self.od_density.rename(columns={'key_0':zone.index.name}, inplace=True)
        self.od_density.set_index(zone.index.name, inplace=True)

        # Add in features for analysis
        self.od_density = self.od_density.fillna(0)
        self.od_density['origin_trip_density'] = self.od_density.origin_trips/self.od_density.origin_trips.sum()
        self.od_density['destination_trip_density'] = self.od_density.destination_trips/self.od_density.destination_trips.sum()
        self.od_density['origin_diff'] = self.od_density['origin_trip_density'] - self.od_density[f'{o_activity}_density']
        self.od_density['destination_diff'] = self.od_density['destination_trip_density'] - self.od_density[f'{d_activity}_density']


    def plot_validate_spatial_density(self, title_1, title_2, density_metric, density_trips, cmap='coolwarm'):
        """
        Creates a spatial plot between input densities and resulting trips to validate trips spatially align with input densities.
        :params title_1, title_2: str input for plot title names.
        :params density_metric: the measure for density output from the above dataframe, in the format of 'activity_density'
        :params density_trips: the measure of trips that require validation, either 'origin_trips' or 'destination_trips'.
        """
        
        fig, ax = plt.subplots(1, 2, figsize=(20,10))

        self.od_density.plot(density_metric, ax=ax[0], cmap=cmap)
        ax[0].axis('off')
        ax[0].set_title(title_1)

        self.od_density.plot(density_trips, ax=ax[1], cmap=cmap)
        ax[1].axis('off')
        ax[1].set_title(title_2)

        im = plt.gca().get_children()[0]
        cax = fig.add_axes([1,0.2,0.03,0.6]) 
        plt.colorbar(im, cax=cax)

        return fig

    def plot_compare_density(self, title_1, title_2, o_activity, d_activity):
        """
        Compares density of input origin/destination activities and trips. As density of locations increases, so should trips.
        :params title_1, title_2: str input for plot title names.
        :params o_activity, d_activity: str of activities that are used to measure density of locations
        """
        
        fig, ax = plt.subplots(1, 2, figsize=(15,7))

        m1,b1 = np.polyfit(self.od_density[o_activity], self.od_density.origin_trip_density, 1)
        m2,b2 = np.polyfit(self.od_density[d_activity], self.od_density.destination_trip_density, 1)

        ax[0].scatter(x=o_activity, y='origin_trip_density', data=self.od_density)
        ax[0].plot(self.od_density[o_activity], (m1*self.od_density[o_activity] + b1), label = 'y = {:.2f} + {:.2f}*x'.format(m1, b1))
        ax[0].legend(loc='lower right') 
        ax[0].set_title(title_1)

        ax[1].scatter(x=d_activity, y='destination_trip_density', data=self.od_density)
        ax[1].plot(self.od_density[o_activity], (m2*self.od_density[o_activity] + b2), label = 'y = {:.2f} + {:.2f}*x'.format(m2, b2))
        ax[1].legend(loc='lower right') 
        ax[1].set_title(title_2)

        return fig

    def plot_density_difference(self, title_1, title_2, cmap='coolwarm'):
        """
        Creates a spatial plot of the difference between input and output densities.
        :params title_1, title_2: str input for plot title names.
        """
        
        fig, ax = plt.subplots(1, 2, figsize=(20,10))

        self.od_density.plot('origin_diff', ax=ax[0], cmap=cmap)
        ax[0].axis('off')
        ax[0].set_title(title_1)

        self.od_density.plot('destination_diff', ax=ax[1], cmap=cmap)
        ax[1].axis('off')
        ax[1].set_title(title_2)

        im = plt.gca().get_children()[0]
        cax = fig.add_axes([1,0.2,0.03,0.6]) 
        plt.colorbar(im, cax=cax)

        return fig

