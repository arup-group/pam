import geopandas as gp
import matplotlib
from matplotlib import pyplot as plt
import random
import pandas as pd

import pam
from pam.activity import Activity, Leg
from pam.variables import END_OF_DAY
from pam.utils import minutes_to_datetime as mtdt


class CreateDistribution:
    """
    Returns a distribution and corresponding plot based on input hourly demand values.
    The resulting distribution can be used to sample time of day of activities or number of repetition of activities.
    """

    def interpolate(self, i, ai, a, bi, b):
        """
        :param i, ai, a, bi, b: input values to build distribution between values a and b
        :return: distribution between a and b
        """
        return a + (i-ai) * (b-a) / (bi-ai)

    def build_distribution(self, bins, pivots, total=None):
    
        """
        Builds a dict distribution based on bins (ie hours) and "pivots" (hourly demand)
        :return: distribution based on defined bins and pivots.
        """
    
        distribution = {}
    
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
                    distribution[i] = self.interpolate(i, ka, pivot_a, kb, pivot_b)
                else:
                    continue       
        
        if total is not None:
            dist_sum = sum(distribution.values())
            for i in bins:
                distribution[i] = (distribution[i]/dist_sum)*total

        return distribution

    def plot_distribution(self, build_distribution, plot_title, x_label, y_label):

        """
        Plots distribution to validate the distribution aligns with expected hourly demand.
        """

        fig, ax = plt.subplots(figsize=(10,4))
        ax.bar(list(build_distribution.keys()), list(build_distribution.values()))
        ax.plot(list(build_distribution.keys()), list(build_distribution.values()), c = 'orange')
        ax.set_title(plot_title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)


### Samplers

class FrequencySampler: # rename to FrequencySampler?
    """
    Object for initiating and sampling from frequency weighted distributing
    """
    def __init__(self, dist, freq=None):
        self.distribution = dist
        self.frequency = freq
        
    def sample(self):
        """
        :param n: number of samples to be returned
        :return: single object or list of objects sampled from distribution
        """
        return random.choices(self.distribution, weights=self.frequency, k=1)[0]
    
    def samples(self, n=1):
        """
        :param n: number of samples to be returned
        :return: single object or list of objects sampled from distribution
        """
        return random.choices(self.distribution, weights=self.frequency, k=n)

class InputDemand:

    """
    Object to build a dataframe that estimates demand and builds constraints to determine a tour sequence.
    In this object, demand is defined as density of locations and constraint is distance between zones.
    TODO - Enable other forms of demand and constraints (i.e, demand Flows, Travel Time between zone constraint)
    """

    def facility_density(self, facilities, zones, zone_id, o_activity, d_activity):
        """
        :param: facilities, zones, zone_id, and od activities (str).
        :return: origin and destination density.
        """
        facility_zone = gp.sjoin(facilities, zones, how='inner', op='intersects')

        # Below could be a for loop to create two dataframes.
        o_density = facility_zone[facility_zone['activity']==o_activity].groupby(zone_id).agg({'activity':'count'}).reset_index()
        o_density['density'] = o_density['activity']/o_density['activity'].sum()

        d_density = facility_zone[facility_zone['activity']==d_activity].groupby(zone_id).agg({'activity':'count'}).reset_index()
        d_density['density'] = d_density['activity']/d_density['activity'].sum()

        return o_density, d_density

    def od_distance(self, zones):
        
        """"
        Create an od dataframe from the zones data that calculates distance between zone centroids.
        This code seems similar in principal to the "write_od_matrices" function, but needs to be rewritten slightly.
        """

        # Create copies of zones file to create an od dataframe.
        df_origin = zones.copy()
        df_origin['centroid'] = df_origin['geometry'].centroid
        cols = df_origin.columns

        df_destination = df_origin.copy()
        
        # Name columns as origin or destination.
        o_cols = {cols[i]:f'o_{cols[i]}' for i in range(len(cols))}
        d_cols = {cols[i]:f'd_{cols[i]}' for i in range(len(cols))}

        df_origin.rename(columns=o_cols, inplace=True)
        df_destination.rename(columns=d_cols, inplace=True)

        # For loop to create od dataframe. 

        df_od = []

        for k in range(len(df_destination)):
            data_d = {i:df_destination[i][k] for i in df_destination}
            for j in range(len(df_origin)):
                data_o = {i:df_origin[i][j] for i in df_origin}
                data_o.update(data_d)
                df_od.append(data_o)

        df_od = pd.DataFrame(df_od)


        # Ideally, would like to not have to do the below steps. It would be better if the geometry types maintained their
        # type when entered into a dictionary, this would allow for distance to be calculated within the for-loop, possibly.

        # When storing geometry types into dictionaries, they become objects. Now, they need to return to their geometry type.
        geo_cols = ['o_geometry', 'd_geometry', 'o_centroid', 'd_centroid']
        for i in geo_cols:
            df_od[i] = gp.GeoSeries(df_od[i])

        # Adding in a distance metric.
        df_od['distance'] = 0
        for i in range(len(df_od)):
            df_od['distance'].loc[i] = (df_od['o_centroid'].loc[i].distance(df_od['d_centroid'].loc[i])*1.4)/1000

        return df_origin, df_destination, df_od


# Class: Stop Location & Sequence? Sequence the stops, we can have this be random or "greedy" or something else.

class TourSequence:
    """
    Object samples destinations based on the destination density and develops a tour sequence.
    """

    
    def dzone_sampler(self, d_density, o_zone, df_od, dist_threshold, dist_id, zone_id):
        """
        :params: d_density and df_od from InputDemand object, o_zone, dist_str (usually 'distance'), zone_id
        :return: sampled d_zone. 
        """
        
        dest_list = df_od[(df_od[f'o_{zone_id}']==o_zone) & (df_od[dist_id] <= dist_threshold)][f'd_{zone_id}']
        d_density_threshold = d_density[d_density[zone_id].isin(dest_list)]
        d_zone = FrequencySampler(list(d_density_threshold[zone_id]), list(d_density_threshold['density']))

        return d_zone

    def stop_sequence(self, stops, d_density, o_zone, df_od, dist_threshold, dist_id, zone_id, facility_sampler, o_loc, d_activity):
        """
        Creates a sequence for a number of stops. Sequence is determined by distance from origin. 
        :params stops: # of stops, this could be one or sampled from a distribution
        :params d_density, df_od: from InputDemand
        :params dist_threshold: maximum distance allowed between origin and destination centroids.
        :params dist_id: str, usually 'distance'
        :params zone_id: str
        :params facility_sampler: returned object from FacilitySampler
        :params d_activity: str of destination activity.
        :returns: d_zone and d_loc (dataframe of sequenced destinations)

        TODO - Function to produce a sequence that minimises distance between stops. 
        """

        d_seq = []

        for j in range(stops):
        # select a d_zone within threshold distance, eventually we can subset the o_d matrix to within thershold.
            d_zone = self.dzone_sampler(d_density, o_zone, df_od, dist_threshold, dist_id, zone_id).sample()
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

        return d_zone, d_loc
    

class ActivityDuration:
    """
    Object to estimate the distance, journey time, and stop time of activities. 
    Final function of activity_duration combines these three functions to output parameters required to build tour plans.
    """

    def model_distance(self, o, d, scale=1.4):
        """
        Get distance between two shapely points
        """
        return o.distance(d) * scale                                                                                                                 

    def model_journey_time(self, distance, speed): # speed default of 40000/3600
        """
        distance in m
        speed as m/s
        """
        return distance / speed

    def model_stop_time(self, time, maxi, mini): # maxi=3600, mini=600
        """
        time in s
        """
        return max([mini, min([time, maxi])]) #  100% of estimated journey time

    def activity_duration(self, o_loc, d_loc, end_tm, speed, maxi, mini):
        """ 
        Estimate Activity Duration. This calculation helps check for activities that go beyond End of Day.
        """
        trip_distance = self.model_distance(o_loc, d_loc)
        trip_duration = self.model_journey_time(trip_distance, speed)
        stop_duration = self.model_stop_time(trip_duration, maxi, mini)

        start_tm = end_tm
        end_tm = end_tm + int(trip_duration/60)

        return stop_duration, start_tm, end_tm


class TourPlan:

    def tour_activity(self, agent, k, zone, loc, activity_type, time_params):
        """
        Add activity to tour plan.
        :params activity_time: str, current function recognises depot (origin activity) and return.
        :params time_params: dictionary of time_params to minimise passing multiple variables. 
        """
        
        # This below function works when activity is depot -> delivery -> delivery, a different logic is needed for return.
        if activity_type == 'depot':
            start_tm = 0
            end_tm = (time_params['hour']*60) + time_params['minute']
            seq = 1
            act = activity_type
        elif activity_type == 'return_depot':
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

    def tour_leg(self, agent, k, o_zone, o_loc, d_zone, d_loc, start_tm, end_tm):
        """ 
        Leg to Next Delivery.
        :params start_tm, end_tm: obtained from ActivityDuration.
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

    def return_depot(self, agent, k, o_zone, o_loc, d_zone, d_loc, end_tm, speed):
        """ 
        Driver returns to depot, from their most recent stop to the origin location.
        Arguably, this function may not be required as it is a collection of other functions.
        """

        trip_distance = ActivityDuration().model_distance(o_loc, d_loc)
        trip_duration = ActivityDuration().model_journey_time(trip_distance, speed)

        start_tm = end_tm
        end_tm = end_tm + int(trip_duration/60)

        end_tm = self.tour_leg(agent=agent, k=k, o_zone=d_zone, o_loc=d_loc, d_zone=o_zone, d_loc=o_loc, start_tm=start_tm, end_tm=end_tm)

        time_params = {'start_tm':end_tm, 'end_tm':END_OF_DAY}
        end_tm = self.tour_activity(agent=agent, k=k, zone=o_zone,loc=o_loc,activity_type='return_depot',time_params=time_params)


        return end_tm

