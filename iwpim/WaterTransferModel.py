import sys
import copy
import collections
from collections import Counter
from copy import deepcopy
from Functions import *
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator
import matplotlib.pyplot as plt

#The Class " Transmission Canal" describe the behavior of transmission lines, in a power system.
#Input: Requests from Zones of diffferent zones  
#Output: A dictionary with the utility names and the amount of power transmitted 	
class TransmissionConduit(AtomicDEVS):
	def __init__(self, name=None, capacity = 0, origin = None, destination = None):
		# Always call parent class' constructor FIRST:
		AtomicDEVS.__init__(self, name)
		
		#Initialization of all variables in the class "TransmissionLine"
		self.state = "idle" 
		self.elapsed = 0
		self.name = name #Name 
		self.capacity = capacity #Physical limitation 
		self.origin = origin 
		self.destination = destination 
		
		#Conduit capacity
		self.capacity = float(self.capacity)
		self.conduitCapacity = float(self.capacity)

		self.total_time = 0	#Total time of simulation	
		
		#List specifying the request from Zones format 
		self.WaterRequested = []
		
		#List of zones where water is transfered to
		self.WaterTransfered = [] #Amount of water transfered 
		

		
		#Name of input/output ports used
		#Input port of the class, receiving from the Zone the request for additional amount of water 
		self.RequestFromStorage = self.addInPort(name="RequestFromStorage") 
		#Input port of the class, receiving response from Zone specifying the amount of power available to share 
		self.ResponseFromStorage  = self.addInPort(name="ResponseFromStorage") 
		
		#Output port of the class, sending response to Zone specifying the amount of water available to spare 
		self.ResponseToStorage  = self.addOutPort(name="ResponseToStorage") 
		#Output port of the class, sending message to the Zone, specifying the actual amount of power transmitted
		self.RequestToStorage = self.addOutPort(name="RequestToStorage") 


		self.transCapUsed = 0
		self.transCapUsed_value	= []
		self.transCapUsedAverage_value = 0
		
	def extTransition(self, inputs):
	#External Transition Function
		self.total_time += self.elapsed #Update the total time for the simulation
		
		requestFromStorage = inputs.get(self.RequestFromStorage)
		responseFromStorage = inputs.get(self.ResponseFromStorage)  

		self.conduitCapacity = float(self.conduitCapacity)
		self.WaterRequested = [] 
		self.WaterTransfered = []

		if self.state == "idle" and requestFromStorage != None :
			self.requestFromStorage  = requestFromStorage

			#print ("req from stoj...................", self.requestFromStorage)
			for rqst in self.requestFromStorage:
				if self.capacity == 0: # No conduit (or transfer agreement)
					#Amount of water requested
					self.WaterRequested.append({'name': rqst.get('name'), 'quantity': 0,
											 'origin': rqst.get('zone')})
				else: # Existing canal 
					self.WaterRequested.append({'name': rqst.get('name'), 'quantity': rqst.get('quantity'),
											 'origin': rqst.get('zone')})
			
			self.state = "request"
		
		elif self.state == "wait" and responseFromStorage != None : 
			self.responseFromStorage = responseFromStorage
			
			#print ("resp", self.responseFromStorage)

			for rsp in self.responseFromStorage: # There is a conduit 

				# Make sure the amount of water being transfered is within the physical constraints
				if self.conduitCapacity < float(rsp.get('quantity')):
					self.WaterTransfered.append({'conduit': self.name, 'name': rsp.get('name'), 'quantity': self.conduitCapacity ,
									 'destination': rsp.get('destination'), 'origin': rsp.get('origin')})
					self.conduitCapacity = 0
				else:
					self.WaterTransfered.append({'conduit': self.name, 'name': rsp.get('name'), 'quantity': rsp.get('quantity'),
									 'destination': rsp.get('destination'), 'origin': rsp.get('origin')})
					self.conduitCapacity -= rsp.get('quantity')

					#Conduit capacity used
				if self.capacity == 0:
					self.transCapUsed = 0
				else:
					self.transCapUsed = 1 - self.conduitCapacity/float(self.capacity) 


			# Graph variable ########################################################
			self.transCapUsed_value.append(self.transCapUsed) #Conduit capacity used
			self.transCapUsedAverage_value = sum(self.transCapUsed_value)/len(self.transCapUsed_value) # Avg conduit capacity usage
			##############################################################################
			
			# Re-initialize the conduit capacity for next time unit
			self.conduitCapacity = self.capacity

			self.state = "transfer"
						
		else:
			print ("ERROR in Ext Trasnfer conduit %s" %self.name)
		return self.state 
							
	def outputFnc(self):
	# Output Funtion, specifying the output to send to the Zone
		if self.state == "request":
			return {self.RequestToStorage: [copy.copy(self.WaterRequested)]}
			
		elif self.state == "transfer":
			#print ("water transfered to storaje -------------", self.WaterTransfered)
			return {self.ResponseToStorage: [copy.copy(self.WaterTransfered)]}
		
		else:
			return {}
			
	def timeAdvance(self):
	# Time advanse function
		if self.state == "idle" or self.state == "wait":
			return INFINITY
		elif self.state == "request" or self.state == "transfer":
			return 0		 
		else:
			raise DEVSException(\
				"unknown state <%s> in T_Line advance function"\
				% self.state) 
				
				
	def intTransition(self):
		self.total_time += self.timeAdvance()
		if self.state == "request":
			self.state = "wait"			
		elif  self.state == "transfer" :
			self.state = "idle"		
		else:
			print ("T_Line Error in Internal Transition Func")
		return self.state    