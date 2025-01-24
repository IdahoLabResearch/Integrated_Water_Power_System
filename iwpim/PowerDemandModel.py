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



class PowerDemand(AtomicDEVS):
	#def __init__(self, name=None, zone):
	def __init__(self, zone = None):
		# Always call parent class' constructor FIRST:
		AtomicDEVS.__init__(self, zone)
		self.state = "idle" 
		self.elapsed = 0
		self.zone = zone

		self.total_time = 0	#Total time of simulation
		self.totaltime_value = []
		
		#Read the demand from csv file 
		file_path = r'C:/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO PRojects/FY21/Model_LatestVersion'
		#file_path = r'/Users/tobad/Library/CloudStorage/OneDrive-IdahoNationalLaboratory/INL_PROJECTS/WPTO Projects/FY21/Model_LatestVersion'

		os.chdir(file_path)

		real = file_path + r'/Data/powerDemand.csv'
		self.powerNeeded = {} 
		self.powerNeeded['zone'] = self.zone 
		self.demandMet = 0
		
		for elmt in readPowerDemand(real):
			if elmt == self.powerNeeded['zone']: #Make sure the name of the demand mathces, so the right demad is processed. 
				self.powerDemand = readPowerDemand(real)[elmt]

		#Name of input/output ports used
		self.PowerDemand = self.addOutPort(name="PowerDemand") #Message to dispatcher indicating the anount of power needed		
		self.PowerSupplied = self.addInPort(name="PowerSupplied") 	#Message from dispatcher, indicating the power met 


	def extTransition(self, inputs):
	#External Transition Function
		self.total_time += self.elapsed 	
		
		#Message from the Dispatcher, specifying the amount of demand met 
		powerSupplied = inputs.get(self.PowerSupplied)

		if self.state == "wait" and powerSupplied != None:
			#Compute the % of demand met 
			self.powerSupplied = powerSupplied
			for pwr  in powerSupplied[0]:
				#Make sure the locations match
				if pwr.get('name') == self.powerNeeded['zone']: #Make sure the locations match
					self.demandMet = float(pwr.get('quantity')[1])  #Power demand met 
					break
			self.state = "advance"
		else:
			print ("ERROR in demand Atomic model EXTERNAL TRANSITION FUNCTION, ZONE : __ %s") %self.zone
		return self.state 

		
	def intTransition(self):
	#Internal Transition Function
		self.total_time += self.timeAdvance()
		
		
		if self.state == "idle":
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


		if  self.state == "send" : 
			#power demand
			self.powerNeeded['quantity'] = self.powerDemand[int(self.total_time)%180]
			return {self.PowerDemand: [copy.copy(self.powerNeeded)]}
		else:
			return {}
				
	def timeAdvance(self):
	# Time advanse function
		if self.state == "advance":
			return 1
		elif self.state == "idle" or self.state == "send":
			return 0
		elif self.state == "wait":
			return INFINITY	
		else:
			raise DEVSException (\
				"unknown state <%s> in demand Atomic model Advance function"\
				 % self.state)
