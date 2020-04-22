import os
import pandas as pd
from pam.activity import Plan
from pam.core import Population

# 1.Get unique values from ozone and dzone
# 2.How do i count pid by ozone and dzone? (= count_data)
# 3.Create dataframe index pd.DataFrame(count_data, columns = dzone, index=ozone )
# 4.Write csv (df.to_csv('OD_matrices.csv'))

path_to_repo = r'C:\Users\Iseul.Song\PythonProjects\pam'
trips = pd.read_csv(os.path.join(path_to_repo, 'example_data\example_travel_diaries.csv'))
print('done')
def extract_od(population):
	
	population = Population()
	ozone = trips.ozone.unique()
	dzone = trips.dzone.unique()

	trips.pivot_table(values='dzone', index='ozone', columns='dzone', fill_value=0, aggfunc=len)
	

	
	# for pid in population.people:
	# ozone = trips.ozone
	# dzone = trips.dzone 
	# pd.DataFrame(count_data, columns = dzone, index=ozone )


### Do i need to make a class inestead of function?? ###
# class od_matrix(Population):
# 	def _init_(self, ozone, dzone):
# 		super()._init_(self)
# 		self.ozone = ozone
# 		self.dzone = dzone

# 	def write(self):
	


