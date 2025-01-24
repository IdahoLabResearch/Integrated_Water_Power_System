import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy
import csv 

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

from Functions import *


import random
from pypdevs.simulator import Simulator

import matplotlib.pyplot as plt
import numpy as np
import pylab 
import datetime


class PowerDispatch(AtomicDEVS):
	def __init__(self, name=None, zone=None):
		
		AtomicDEVS.__init__(self, name)
		self.state = "idle"
		self.elapsed = 0
			

		#Initialization of all variables in the class "Dispatcher"
		self.name = name #Name of the dispatcher
		self.zone = zone #Zone of the dispatcher
		self.elapsed = 0
		self.total_time = 0	#Total simulation time
		self.total_time_value = []	#Total simulation time

		self.demandWaterToBeMet = {} 
		self.demandPowerToBeMet = {}
		self.availableCapacity = {} #Available Capacity per generator
		self.TotalAvailableCapacity = 0 #Total power capacity, considering all generators combined 
		self.TotalDemand = 0 #Total demand, combining all loads requests
		self.UsedForPower = 0
		self.UsedForWater  = 0	
		self.TotalDemandPower = 0
		self.TotalDemandWater = 0	
		self.totalPumpEnjReq = 0
		self.hydro_value = []
		self.grid_value = []
		self.demandWaterMet_list = []
        
		#Name of input/output ports used in this class
		self.DemandForPower = self.addInPort(name="DemandForPower") #DemandFromLoad
		self.DemandForWater = self.addInPort(name="DemandForWater") #DemandFromLoad
		#Input port receiving the generation capacity
		self.AvailablePower= self.addInPort(name="AvailablePower") 
		
		#Output port specifying the amount of demand met 
		self.SupplyToDemand = self.addOutPort(name="SupplyToDemand") 
		self.SupplyToWater = self.addOutPort(name="SupplyToWater") 
		self.SupplyToPump = self.addOutPort(name="SupplyToPump") 
		self.SupplyToSource = self.addOutPort(name="SupplyToSource") 

				
	def extTransition(self, inputs):
	#External Transition Function
	#Receives input from the load, the generator and the TL (if necessary), and dispatches energy
		self.total_time += self.elapsed #Update the total time for the simulation
				
		demandForWater = inputs.get(self.DemandForWater) #Message from water demand system, to power pumps and carry water
		demandForPower = inputs.get(self.DemandForPower) #Message from power demand
		availablePower = inputs.get(self.AvailablePower) #Message from all power sources
		
		if self.state == "idle" and (demandForPower != None and availablePower != None and demandForWater != None):
			self.TotalAvailableCapacity = 0
			self.TotalDemand = 0
			self.UsedForPower = 0
			self.UsedForWater = 0 
			self.TotalDemandPower = 0
			self.TotalDemandWater = 0
			self.demandWaterMet_list = []
			self.totalPumpEnjReq = 0 
            
			#power demand 
			for item in demandForPower:
				self.demandForPower = demandForPower
				#  total amount of power needed 
				self.TotalDemandPower += float(item.get('quantity'))
			
			#power avaialble in the system 
			for item in availablePower:
				self.availablePower = availablePower
				self.TotalAvailableCapacity += item.get('quantity')
			
			#Total power available
			self.totalAvailPower = self.TotalAvailableCapacity

			#power for  water distribution
			for item in demandForWater: #Energy requirement from water  pumps
				self.demandForWater = demandForWater

                # Total energy requirement from pumps  
				self.TotalDemandWater += float(item.get('quantity')) 

            # Total demand, including water and power 
			self.TotalDemand = self.TotalDemandWater + self.TotalDemandPower

            #Energy set apart for water pump 
			self.TotalAvailableCapacity -= self.TotalDemandPower
			
			# Check if there is enough water for water pump
			if self.TotalAvailableCapacity >0:
				self.TotalAvailableCapacity = self.TotalAvailableCapacity
			else:
				self.TotalAvailableCapacity = 0

			#Energy requirement from water  pumps
			for item in demandForWater: 
                #If outage 
				if item.get('outage') == "Yes":
					self.demandWaterMet = DemandSupply_Outage(item, self.TotalAvailableCapacity)
				else:
					self.demandWaterMet = DemandSupply(item, self.TotalAvailableCapacity) 

				# List of water demand to be met, if pump energy requirement are met 
				self.demandWaterMet_list.append(self.demandWaterMet)
                
			#distribute power to customers
			self.demandPowerToMeet = PowerSupplyBalance(self.demandForPower, self.totalAvailPower) 

			#Rank power sources based on cost before distribution 
			self.availablePower = RankEnergySources (self.availablePower)

			# power sources redistribution 
			self.PowerSourceUsed = EnergySourceUsage(self.availablePower, self.TotalDemand)

			self.state = "respondToPowerDemand"	

		#Graphing variables =====================================================================
					
					
		#=====================================================================================
		else:
			print ("ERROR in power DISPATCHER model EXTERNAL TRANSITION FUNCTION") 
		
		#print ("total time is %f  ------------------------ ", self.total_time)
		self.total_time_value.append(self.total_time)
        #######################################################################
        
		return self.state 
		
	def intTransition(self):
	#Internal Transition Function
		self.total_time += self.timeAdvance()
				
		if self.state == "respondToPowerDemand" : 
			self.state = "wait"

		elif self.state == "wait" : 
			self.state = "wait_1"
		
		elif self.state == "wait_1" : 
			self.state = "wait_2"
			
		elif self.state == "wait_2" : 
			self.state = "wait_3"

		elif self.state == "wait_3" : 
			self.state = "wait_4"

		elif self.state == "wait_4" : 
			self.state = "respondToWaterDemand"

		elif self.state == "respondToWaterDemand" : 
			self.state = "idle"
		else:
			print ("ERROR in DISPATCHER Atomic model INTERNAL TRANSITION FUNCTION")
		#print ("power dispatch state is  ", self.state)			
		return self.state   
					  
	def outputFnc(self):
	# Output Funtion.
							
		if self.state == "respondToPowerDemand": 
			#Return the amount of demand met and power needed per generator  
			return {self.SupplyToDemand: [copy.copy(self.demandPowerToMeet)], self.SupplyToSource: [copy.copy(self.PowerSourceUsed)]}
		
		elif self.state == "respondToWaterDemand": 
			# Power set aside for water operatios - pumps and water disp
			return { self.SupplyToWater: [copy.copy(self.demandWaterMet_list)], self.SupplyToPump: [copy.copy(self.demandWaterMet_list)]}
		else:
			return {}
					
			
	def timeAdvance(self):
	# Time advanse function
		if self.state == "idle" :
			return INFINITY 
		elif self.state == "respondToPowerDemand" or self.state == "respondToWaterDemand" or self.state == "wait"\
					or self.state == "wait_1" or self.state == "wait_2" or self.state == "wait_3" or self.state == "wait_4":
			return 0
		else:
			raise DEVSException(\
				"unknown state <%s> in DISPATCHER Atomic model ADVANCE FUNCTION "\
				% self.state) 

