import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy
import os  
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

import matplotlib.pyplot as plt
import numpy as np
from Functions import *

# Those are farms located on a given canal.
# the volume of the water canal remains constant


class WaterDemand(AtomicDEVS):
	#def __init__(self, name=None, zone):
	def __init__(self, name=None, zone = None, canal = None):
		# Always call parent class' constructor FIRST:
		AtomicDEVS.__init__(self, name)
		self.state = "idle" 
		self.elapsed = 0
		self.name = name
		self.canal = canal # The canal that deserves the area/farm
		self.zone = zone

		self.total_time = 0	#Total time of simulation
		
		file_path = r'/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO PRojects/FY21/Model_LatestVersion'
		#file_path = r'/Users/tobad/Library/CloudStorage/OneDrive-IdahoNationalLaboratory/INL_PROJECTS/WPTO Projects/FY21/Model_LatestVersion'

		# Read the demand 
		real = file_path + r'/Data/waterDemand.csv'

		self.waterNeeded = {} #Amount of water needed
		self.waterNeeded['name'] = self.name #Name of the farm
		self.waterNeeded['zone'] = self.zone #Name of the farm		
		self.waterNeeded['canal'] = self.canal #Name of the farm		
		

		for elmt in readWaterDemand(real): #Read the demand
			if elmt.get('name') == self.waterNeeded['name']:
				self.waterDemand = elmt.get('demand')
				break

		self.demandMet = []
		self.demandMet_Q = []

		#Graph value initialization
		self.waterdemandMet_value = []
		self.waterdemandMet_Q_value = []
		self.waterdemand_value = []
		self.totaltime_value = []
		self.waterSupplied_value = []

		#Name of input/output ports used
		self.WaterDemand = self.addOutPort(name="WaterDemand") #Sending message for power demand 
		
		#Input port of the class, receiving the proportion of demand met from the dispatcher
		self.WaterSupplied = self.addInPort(name="WaterSupplied") 


	def extTransition(self, inputs):
	#External Transition Function
		self.total_time += self.elapsed 	

		#Message from the Dispatcher, specifying the amount of demand met 
		waterSupplied = inputs.get(self.WaterSupplied)

		if self.state == "wait" and waterSupplied != None:
			self.waterSupplied = waterSupplied
			for i in self.waterSupplied[0]:
				if i.get('name') == self.waterNeeded['name']:
					#Amount of water demands met, per farm 
					self.demandMet = i.get('quantity')[1] #Portion of demand met
					self.demandMet_Q = i.get('quantity')[0] #Actual quantity of demand met
					break 
			self.state = "advance"
		else:
			print ("ERROR in demand Atomic model EXTERNAL TRANSITION FUNCTION, ZONE : __ %s") %self.location
		
		#Graph variable #####################################
		self.waterdemandMet_value.append(self.demandMet) #Portion of demand met  
		self.waterdemandMet_Q_value.append(self.demandMet_Q) # Actual demand met  

		self.waterdemand_value.append(self.waterNeeded['quantity']) #water demand  
		self.totaltime_value.append(self.total_time)
		#########################################################

		return self.state 

		
	def intTransition(self):
	#Internal Transition Function
		self.total_time += self.timeAdvance()
	
		if self.state == "idle":
			self.state = "idle_1"
		
		elif self.state == "idle_1":
			self.state = "send"
			
		elif self.state == "send":
			self.state = "wait"
		
		elif self.state == "advance":
			self.state = "idle"
			
		else:
			print ("ERROR in demand Atomic model INTERNAL TRANSITION FUNCTION")	
		return self.state 

    
	def outputFnc(self):
	# Output Funtion, specifying the output to send to the dispatcher
		k = 0
		if  self.state == "send" :
			k += 1 
			if self.total_time >= 2:
				self.total_time -= k
			self.waterNeeded['quantity'] = self.waterDemand[int(self.total_time)] #water needed
			return {self.WaterDemand: [copy.copy(self.waterNeeded)]}
		else:
			return {}
				
	def timeAdvance(self):
	# Time advanse function
		if self.state == "advance":
			return 1
		elif self.state == "idle" or self.state == "send" or self.state == "idle_1":
			return 0
		elif self.state == "wait":
			return INFINITY	
		else:
			raise DEVSException (\
				"unknown state <%s> in demand Atomic model Advance function"\
				 % self.state)
