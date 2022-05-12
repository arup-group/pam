import geopandas as gp
import matplotlib
from matplotlib import pyplot as plt
import random
import pandas as pd
import numpy as np

import pam
from pam.activity import Activity, Leg
from pam.variables import END_OF_DAY
from pam.utils import minutes_to_datetime as mtdt

def interpolate(i, ai, a, bi, b):
    """
    :param i, ai, a, bi, b: input values to build distribution between values a and b
    :return: distribution between a and b
    """
    return a + (i-ai) * (b-a) / (bi-ai)


class PivotDistributionSampler: 
    """
    Returns a distribution and corresponding plot based on input values. The resulting distribution can be sampled
    to select the value of parameters that will be used as inputs for Plan (i.e, time of day, repetition of activities).
    """

    def __init__(self, bins, pivots, total=None):
        """
        Builds a dict distribution based on bins (ie hours) and pivots (i.e, hourly demand). 
        The interpolate function is applied to estimate values within the bin range if the pivot does not have a value.
        :param bins: a range or dictionary of values
        :param pivots: a dictionary of values associated with the bins
        :return: distribution based on defined bins and pivots
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
    
    def sample(self):
        return random.choices(list(self.demand.keys()), list(self.demand.values()), k=1)[0]

class FacilityDensitySampler:

    def __init__(self, facility_zone, zone, activity):
        """
        :param facility_zone: a geodataframe
        :param zone: zones file, used to provide geometry for resulting dataframe
        :param activity: str of selected activity from the facility data
        :return: density of locations for selected activity
        """
        self.density = facility_zone.groupby([facility_zone.index, facility_zone.activity]).agg({'id':'count'}).reset_index()
        self.density.set_index(facility_zone.index.name, inplace=True)
        self.density = self.density[self.density['activity']==activity]
        self.density['density'] = self.density['id']/self.density['id'].sum()
        # Convert back to geodataframe for merging.
        self.density = pd.merge(self.density, zone, left_on = self.density.index, right_on=zone.index, how='left')
        self.density.rename(columns={'key_0':facility_zone.index.name}, inplace=True)
        self.density = gp.GeoDataFrame(data=self.density, geometry='geometry')
        self.density.set_index(facility_zone.index.name, inplace=True) 

    def ozone_sample(self):
        return random.choices(list(self.density.index), list(self.density['density']),  k=1)[0]
    
    def dzone_sample(self, o_zone, df_od, dist_threshold): #ozone is required to make this work. 
        """
        :param o_zone: a single origin zone input
        :param df_od: input origin destination dataframe that estimates distances between the centroid of each o/d pair
        :param dist_threshold: int value set to limit the potential destinations to sample from
        :return: sampled destination zone 
        """
            
        dest_list = df_od.loc[o_zone]
        dest_list = dest_list[dest_list<dist_threshold].index
        density_threshold = self.density[self.density.index.isin(dest_list)]
        
        if len(density_threshold) == 0:
            #print('No destination available, resampling o_zone...')
            raise UserWarning('No destinations within this distance')

        return random.choices(list(density_threshold.index), list(density_threshold['density']), k=1)[0]

class FrequencySampler: 
    """
    Object for initiating and sampling from frequency weighted distributing
    """
    def __init__(self, dist, freq=None):
        self.distribution = dist
        self.frequency = freq
        
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
    

class ActivityDuration: 
    """
    Object to estimate the distance, journey time, and stop time of activities. 
    Final function of activity_duration combines these three functions to output parameters required to build tour plans.
    """

    def model_distance(self, o, d, scale=1.4):
        """
        Model distance between two shapely points
        """
        return o.distance(d) * scale                                                                                                                 

    def model_journey_time(self, distance, speed=40000/3600):
        """
        :param distance: in m
        :param speed: in m/s
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
        return max([mini, min([time, maxi])]) #  100% of estimated journey time

    def model_activity_duration(self, o_loc, d_loc, end_tm, speed=40000/3600, maxi=3600, mini=600):
        """ 
        Estimate Activity Duration, combination of previous three functions to return parameters for next activity.
        :param o_loc: origin facility
        :param d_loc: destination facility
        :param end_tm: most recent end time of previous leg
        :param speed: speed of vehicle
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


class TourPlan:
    
    def sequence_stops(self, stops, ozone_sampler, dzone_sampler, df_od, dist_threshold, dist_id, facility_sampler, o_activity, d_activity):
        """
        Creates a sequence for a number of stops. Sequence is determined by distance from origin 
        :params stops: # of stops, this could be one or sampled from a distribution
        :params ozone_sampler: sampler for origin location
        :params dzone_sampler: sampler for destination location
        :params df_od: origin/destination matrix with distance information
        :params dist_threshold: maximum distance allowed between origin and destination centroids
        :params dist_id: str, usually 'distance', depends what is in o/d matrix
        :params facility_sampler: returned object from FacilitySampler
        :params o_activity: str of origin activity
        :params d_activity: str of destination activity
        :returns: d_zone and d_loc (dataframe of sequenced destinations)

        TODO - Function to produce a sequence that minimises distance between stops. 
        """
        o_zone = ozone_sampler.ozone_sample()
        o_loc = facility_sampler.sample(o_zone, o_activity)

        d_seq = []

        for j in range(stops):
        # select a d_zone within threshold distance
            d_zone = dzone_sampler.dzone_sample(o_zone=o_zone, df_od=df_od, dist_threshold=dist_threshold)
            d_facility = facility_sampler.sample(d_zone, d_activity)
            d_seq.append({
                'stops': j,
                'destination_zone': d_zone,
                'destination_facility': d_facility,
                'distance': ActivityDuration().model_distance(o_loc, d_facility)
            })
    
        d_seq = pd.DataFrame(d_seq)

        # sort distance: furthest facility to closest facility to origin facility. The final stop should be closest to origin.
        d_seq = d_seq.sort_values(by=dist_id)
        d_loc = d_seq['destination_facility'].to_dict()

        return o_zone, o_loc, d_zone, d_loc

    def add_tour_activity(self, agent, k, zone, loc, activity_type, time_params):
        """
        Add activity to tour plan.
        :params agent: agent for which the activity will be added to Plan
        :params k: when used in a for loop, k populates the next sequence value
        :params zone: zone where activity takes place
        :params loc: facility location where activity takes place
        :params activity_time: str, this function has specific logic for 'depot' and 'return_origin', it assumes all other activities are 'delivery'
        :params time_params: dictionary of time_params that may be time samplers or times of previous journeys
        :return: end_tm of activity
        """
        
        if activity_type == 'depot':
            start_tm = 0
            end_tm = (time_params['hour']*60) + time_params['minute']
            seq = 1
            act = activity_type
        elif activity_type == 'return_origin':
            start_tm = time_params['start_tm'] # end_tm
            end_tm = time_params['end_tm']  # END_OF_DAY we'll let pam trim this to 24 hours later
            seq = k+2
            act = 'depot'
        else:
            start_tm = time_params['end_tm']
            end_tm = time_params['end_tm'] + int(time_params['stop_duration']/60)
            seq = k+2
            act = activity_type
        
        # Activity plan requires mtdt format, but int format needs to passed for other functions to calculate new start time.
        # END_OF_DAY as is already in mtdt format, so adding an exception to keep mtdt format separate specifically for end_time.
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
        :returns: end_tm
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

    def add_return_origin(self, agent, k, o_zone, o_loc, d_zone, d_loc, end_tm, speed=40000/3600):
        """ 
        Driver returns to depot, from their most recent stop to the origin location.
        :params agent: agent for which the leg & activity will be added to Plan
        :params k: when used in a for loop, k populates the next sequence value
        :params o_zone: origin zone of leg & activity
        :params o_loc: origin facility of leg & activity
        :params d_zone: destination zone of leg & activity
        :params d_loc: destination facility of leg & activity
        :params end_tm: obtained from ActivityDuration object
        :params speed: default setting of 50km/hr
        :return: end_tm
        """

        trip_distance = ActivityDuration().model_distance(o_loc, d_loc)
        trip_duration = ActivityDuration().model_journey_time(trip_distance)

        start_tm = end_tm
        end_tm = end_tm + int(trip_duration/60)

        end_tm = self.add_tour_leg(agent=agent, k=k, o_zone=d_zone, o_loc=d_loc, d_zone=o_zone, d_loc=o_loc, start_tm=start_tm, end_tm=end_tm)

        time_params = {'start_tm':end_tm, 'end_tm':END_OF_DAY}
        end_tm = self.add_tour_activity(agent=agent, k=k, zone=o_zone,loc=o_loc,activity_type='return_origin',time_params=time_params)


        return end_tm

class ValidateTourOD:

    def __init__(self, trips, zone, ozone_sampler, dzone_sampler, o_activity, d_activity):
        """
        Create a dataframe that counts the number of origin and destination activities. 
        Merge this against the density information from the input origin and destination samplers.
        :params trips: dataframe, the legs.csv output after building population
        :params zone: zones geodataframe
        :params ozone_sampler, dzone_sampler: samplers containing density dataframes
        :params o_activity, d_activity: activities utilised to build the ozone_sampler and dzone_sampler
        :returns: geodataframe of origin trips, destination trips, and origin/destination densities for each zone
        """

        df_trips_o = trips[trips['origin activity']==o_activity].groupby(['ozone']).agg({'pid':'count'}).reset_index()
        df_trips_o.rename(columns={'pid':'origin_trips'}, inplace=True)
        df_trips_o.set_index('ozone', inplace=True)

        df_trips_d = trips[trips['destination activity']==d_activity].groupby(['dzone']).agg({'pid':'count'}).reset_index()
        df_trips_d.rename(columns={'pid':'destination_trips'}, inplace=True)
        df_trips_d.set_index('dzone', inplace=True)

        # Create a dataframe to plot od trips and compare against facility density and flows density.
        self.od_density = zone.copy()#.reset_index()

        # Merge in trips information
        self.od_density = pd.merge(self.od_density, df_trips_o, left_on=self.od_density.index, right_on=df_trips_o.index, how='left')
        self.od_density = pd.merge(self.od_density, df_trips_d, left_on='key_0', right_on=df_trips_d.index, how='left')

        # Merge in density information
        self.od_density = pd.merge(self.od_density, ozone_sampler.density['density'], left_on='key_0', right_on=ozone_sampler.density.index, how='left')
        self.od_density.rename(columns={'activity':f'{o_activity}_activity','density':f'{o_activity}_density'}, inplace=True)
        self.od_density = pd.merge(self.od_density, dzone_sampler.density['density'], left_on='key_0', right_on=dzone_sampler.density.index, how='left')
        self.od_density.rename(columns={'activity':f'{d_activity}_activity','density':f'{d_activity}_density'}, inplace=True)

        self.od_density.rename(columns={'key_0':zone.index.name})
        self.od_density.set_index(zone.index)


    def plot_validate_spatial_density(self, title_1, title_2, density_metric, density_trips, cmap='coolwarm'):
        """
        Creates a comparison plot between input densities and resulting trips to validate trips spatially align with input densities.
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

    def plot_compare_density(self, title_1, title_2, o_activity, d_activity):
        """
        Compares density of input origin/destination activities and trips. As density of locations increases, so should trips.
        :params title_1, title_2: str input for plot title names.
        :params o_activity, d_activity: str of activities that are used to measure density of locations
        """
        
        fig, ax = plt.subplots(1, 2, figsize=(15,7))

        ax[0].scatter(x=o_activity, y='origin_trips', data=self.od_density)
        ax[0].set_title(title_1)

        ax[1].scatter(x=d_activity, y='destination_trips', data=self.od_density)
        ax[1].set_title(title_2)
