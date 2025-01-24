import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random

from Functions import *

from operator import add

import numpy as np


#Considered as the main source, where all canals get the water from. 
# Think of it as the reservoir, which update capacity accordingly 

class WaterSource(AtomicDEVS): 
    #Each water source is characterized by those parameters
	def __init__(self, name=None, zone = None ): #Add characteristics of the generator
      
		# Always call parent class' constructor FIRST:
		AtomicDEVS.__init__(self, name)		
		
  #Initialization of all variables of the class 
		self.state = "idle" #initial state
		self.elapsed = 0
		self.name = name #Name of the source
		#self.location = location 
		
		#A dictionary specifying name and the capacity for usage of the utility {'name':'generator_name', 'capacity': quantity}
		#self.supply['location'] = self.location
		self.supply = {}
		self.supply['name'] = self.name
		self.supply['capacity'] = WaterSourceCapacity(self.name) * WaterForIrrigation(self.name) #Proportion of water used for irrigation

		self.waterSupplied = {} # Amount of water to supply to canals 

		self.total_time = 0 #simulation time 
		self.trackvalue = self.total_time 
		#Graph variables --------------------------------------
		self.capacity_value = []
		self.totaltime_value = []
		#-------------------------------------------------------
		
		#Input and output of the class ----------------------------------------------------------------------------------
		
		#Output messages sent by the agent 
		self.WaterDelivered = self.addOutPort(name="WaterDelivered") #Message sent to the dispatcher indicating amount of water avaialable
		self.WaterRequestReceived = self.addInPort(name="WaterRequestReceived") #Message received from water canal 
		
	def extTransition(self, inputs):
	#External Transition Function, defining state change after receiving input from another class
		self.total_time += self.elapsed #Update the total time for the simulation
				
		waterRequestReceived = inputs.get(self.WaterRequestReceived) #Message received from water canals, from the same location (origin) 
        
		#Receive the amount of water needed per canal 
		if self.state == "idle" and waterRequestReceived != None:
			self.waterRequestReceived = waterRequestReceived #update water capacity 
			for source in self.waterRequestReceived:
				# water to supply canals
				self.supply['capacity'] -= float(source.get('quantity')) #update water capacity 
				self.waterSupplied.update({source.get('name') : source.get('quantity')})

			self.state = "supply"
		return self.state 
		
	def intTransition(self):
	#Internal Transition Function, defining state change internally
		self.total_time += self.timeAdvance()
		
		if self.state == "supply":
			self.state = "idle"
		

		else:		
			print ("ERROR in water supply Atomic model INTERNAL TRANSITION FUNCTION")
		return self.state

							
	def outputFnc(self):
	# Output Funtion, specifying the output to send to the dispatcher
		#Graph variables #######################################################
		self.capacity_value.append(self.supply['capacity']) #water source capacity 
		self.totaltime_value.append(self.total_time)
		
		########################################################################
		if self.state == "supply" :
			return {self.WaterDelivered: [copy.copy(self.waterSupplied)]} 
		
		else:
			return {}
			
			
	def timeAdvance(self):
	# Time advanse function
		if self.state == "supply" :   
			return 0
		elif self.state == "idle" :  
			return 	INFINITY 
		else:
			raise DEVSException(\
				"unknown state <%s> in water Atomic model ADVANCE FUNCTION"\
				% self.state)
				
