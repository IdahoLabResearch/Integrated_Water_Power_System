import sys
import copy
import os 
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator
from itertools import groupby

import matplotlib.pyplot as plt
import numpy as np
from Functions import *


#This class is designed in a way that there is only one pump per canal. 
# So the enj requierement per pump is dependent o the total demand along the very canal. 
class PumpReq(AtomicDEVS):
	#def __init__(self, name=None, zone):
	def __init__(self, name=None, zone=None, outage=None, canal = None):
		# Always call parent class' constructor FIRST:
		AtomicDEVS.__init__(self, name)
		self.state = "idle" 
		self.elapsed = 0
		self.name = name
		self.zone = zone
		self.outage = outage
		self.canal = canal

		self.total_time = 0	#Total time of simulation

		#Read the pumps characteristics
		#file_path = r'C:/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO PRojects/FY21/Model_LatestVersion'
		file_path = r'C:/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO Projects/FY21/Model_LatestVersion'

		os.chdir(file_path)
		pump = file_path + r'/Data/waterPump.csv'
		real = file_path + r'/Data/waterDemand.csv'

		self.energyNeeded = {} #Amount of energy needed
		self.energyNeeded['name'] = self.name #Name of the pump
		self.energyNeeded['zone'] = self.zone #Name of the pump
		self.energyNeeded['outage'] = self.outage #Name of the pump
		self.energyNeeded['canal'] = self.canal #Name of the canal the pump is mounted on

		self.waterToMove = []
		self.energyRequirement = [] 

        # Make sure pumps get the appropriate energy need value 
		for pump in readPump(pump):
			for dmd in aggregateWaterDemand(real):
				if dmd.get('canal') == pump.get('canal'): #Match the canal on which the pump is, with demand from this very canal 
					#Energy requirement given water demand
					if  pump.get('outage') == "No": # Check if there is an outage
						#No outage
						self.energyRequirement.append({'pump': pump.get('name'), 'demand': dmd.get('demand'), 
												'canal': dmd.get('canal'), 'outage':pump.get('outage') })
					else:
						#Outage
						self.energyRequirement.append({'pump': pump.get('name'), 'demand': [0 for d in range(len(dmd.get('demand')))], 
												'canal': dmd.get('canal'), 'outage':pump.get('outage') })
				 
		self.energyMet = [] #Energy met to power pumps

		#Graph value initialization
		self.energydemandMet_value = []  
		self.energydemand_value = []
		self.totaltime_value = []

		#Name of input/output ports used
		self.EnergyRequirement = self.addOutPort(name="EnergyRequirement") #Sending message for power demand 
		
		#Input port of the class, receiving the proportion of demand met from the dispatcher
		self.EnergySupplied = self.addInPort(name="EnergySupplied") 


	def extTransition(self, inputs):
	#External Transition Function
		self.total_time += self.elapsed 	
		
		#Message from the Dispatcher, specifying the amount of demand met 
		EnergySupplied = inputs.get(self.EnergySupplied)
		if self.state == "wait" and EnergySupplied != None:
			#Compute the loss of load using the function "LossOfLoad"
			for i in EnergySupplied[0]:
				if i.get('name') == self.name: #Names of pumps match 
					#Lists of the amount of demands met, per loads 
					self.energyMet.append(i.get('quantity')[1])
					break
			self.state = "advance"
		else:
			print ("ERROR in PUMP Atomic model EXTERNAL TRANSITION FUNCTION, LOCATION : __ %s") %self.location
		
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
			print ("ERROR in Pump Atomic model INTERNAL TRANSITION FUNCTION")	
		return self.state 


	def outputFnc(self):
	# Output Funtion, specifying the output to send to the dispatcher

		if  self.state == "send" : 
			self.energyNeeded['quantity'] = 0
			#power needed for the pump, sent to power dispatch
			
			for enj in self.energyRequirement:
				#Make sure this is the right pump
				if enj.get('pump') == self.name:
				
				#Energy needed for the pump to work, depending on the amount of water to be moved
					self.energyNeeded['quantity'] = enj.get('demand')[int(self.total_time)%180] * 62.43 * 0.030625 * 0.001 * 503

			
			#Graph variables #######################################################
			self.energydemand_value.append(self.energyNeeded['quantity']) #water source capacity 
			self.totaltime_value.append(self.total_time)
			########################################################################

			# E nergy Needed by each pump. Request sent to Dispatcher
			return {self.EnergyRequirement: [copy.copy(self.energyNeeded)]}
		else:
			return {}
				
	def timeAdvance(self):
	# Time advance function
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

# Source for conversion psi to energy requirement #####################################################3
# 1 cf ==> 62.43 lb / 1 psi pressure = 2.31 feet of water head * 0.0004375 mile of of water head
# 1 kWh = 2,655,220 ft-lb = 0.001Mwh = 503 mile
#Formula used is E= w.d (weight of water over distance carried. Source: https://cetulare.ucanr.edu/files/82040.pdf
#####################################################################################################