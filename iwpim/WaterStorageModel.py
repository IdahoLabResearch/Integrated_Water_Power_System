import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy
from itertools import groupby

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
import matplotlib.pyplot as plt

from Functions import *

from operator import add

import numpy as np
import pylab 

#Generator is a class that specifies the behavior of power generators. 
#Input: Message from the class "UnitCommittment", which specifies the name and 
#capacity of committed utilities 
#Output: A dictionary with the power generator name and the capacity available for usage  {'generator_name': capacity}
#capacity is the amount of power generated on an hourly basis. This value is taken out of the list 'commitment'
class WaterStorage(AtomicDEVS): 
    #Each power utility is characterized by the name, type and capacity
    def __init__(self, name=None, zone = None,  capacity = 0, inflow = 0, outflow = 0, quantity = 0): 
        
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
        
        #Initialization of all variables of the class 
        self.state = "idle" #initial state
        self.elapsed = 0
        self.name = name #Name of the storage  
        self.zone = zone #Name of the storage  
        self.capacity = capacity #Capacity of the storage  
        self.inflow = inflow # Inflow of the storage  
        self.outflow = outflow #Outflow of the storage  
        self.quantity = quantity #Quantity of water of the storage  
        
        #A dictionary specifying name and the capacity for usage of the utility {'name':'generator_name', 'capacity': quantity}
        self.supply = {}
        self.supply['name'] = self.name  	
        self.supply['zone'] = self.zone   	
        
        
        self.total_time = 0 #simulation time 
        self.storedQuantityNeeded = 0
        self.waterRemaining = 0
        self.waterToReq = 0 #Water to request to storage in other areas 
        self.waterToShare = {}
        self.waterToDispatch = 0
        self.reqfromConduit = []
        self.waterNeed = 0  #amount of water needed per zone
        self.waterNeedTot = 0 #Total amount of water needed per zone
        #Graph values
        self.waterStored_value = [] #Water stored 
        self.request_value = [] # Water requested 
        self.supply_value = [] # Water provided by storage
        self.totaltime_value = []




        self.capacity = StorageSourceCapacity(self.name) #Original water quantity 
        self.inflow = StorageSourceInflow(self.name) #Storage inflow
        self.outflow = StorageSourceOutflow(self.name) #Storage outflow
        self.quantity = StorageSourceQuantity(self.name) #Quantity of water over time  
        self.waterStored = self.quantity #Current amount of water in the tank 
        
        

        
        #Input and output of the class ----------------------------------------------------------------------------------
        self.ReqforWater = self.addInPort(name="ReqforWater") #Message from dispatcher needing extra water
        self.ReqfromConduit = self.addInPort(name="ReqfromConduit") #Message from conduit needing extra water
        self.RespfromConduit = self.addInPort(name="RespfromConduit") #Message from conduit sending extra water
        
        self.WaterDelivered = self.addOutPort(name="WaterDelivered") #Message sent to dispatcher to provide water 
        self.RespToConduit = self.addOutPort(name="RespToConduit") #Message sent to dispatcher to provide water 
        self.ReqToConduit = self.addOutPort(name="ReqToConduit") #Message sent through conduit to provide water 


    def extTransition(self, inputs):
    #External Transition Function, defining state change after receiving input from another class
        self.total_time += self.elapsed 

        #Message from water water dispatcher
        reqforWater = inputs.get(self.ReqforWater)
        reqfromConduit = inputs.get(self.ReqfromConduit)
        respfromConduit = inputs.get(self.RespfromConduit)
        
        self.waterToReq = 0 #Amount of water requested to other storage in case there is not enough water avaialable 
        self.waterNeed = 0 #Amount of water needed by zone 
        #self.waterNeedTot = 0
        if self.state == "idle" and reqforWater != None :
            self.reqforWater  = reqforWater #Water request from dispatcher 

            for req in  self.reqforWater[0]:
                # Assess storages by zones 
                if req.get('zone') == self.zone:
                    #Amount of water needed by zone 
                    self.waterToUse = 0 # Water quantity available/to be requested
                    self.waterNeed = float(req.get('surplus')*req.get('proportion'))
                    self.waterNeedTot += float(req.get('surplus')*req.get('proportion'))

                    #Compute the new storage capacity    
                    self.waterToUse =  WaterUse(self.waterNeed, self.capacity, self.waterStored, self.inflow, self.outflow)[0] #Water in storage to use
                    self.waterRemaining =  WaterUse(float(req.get('surplus')*req.get('proportion')), self.capacity, self.waterStored, self.inflow, self.outflow)[1] # Water remaining

                    #Update the remaining capacity of storage 
                    self.waterStored =  self.waterRemaining 

                    # Request more water, if constraints allow through conduits 
                    if self.waterRemaining > 0:
                        self.waterToReq = 0
                        self.waterToDispatch += self.waterToUse
                    else:
                        self.waterToReq +=  abs(self.waterToUse) 
                        self.waterToDispatch = 0

            self.supply['quantity'] = self.waterToReq

            self.request_value.append(self.supply['quantity']) #Graph value 

            self.state = "request" # Send request to other zone/storage through transfer lines/conduits
            
        elif self.state == "idle" and reqfromConduit != None :
            self.reqfromConduit = reqfromConduit # Water requested to other storages through conduits

            for rq in self.reqfromConduit[0]:
                if rq.get('origin') != self.zone: #Identify the destination region/zone
                    self.waterToBeTransfered = WaterUse((-rq.get('quantity')), self.capacity, self.waterStored, self.inflow, self.outflow)[0] #Water to distribute, if avaialable
                    self.waterRemaining = WaterUse((-rq.get('quantity')), self.capacity, self.waterStored, self.inflow, self.outflow)[1] #Water remaining 
                    
                    # Amount of water to share with other region
                    self.waterToShare.update({'name': self.name, 'quantity': self.waterToBeTransfered, 'origin': self.zone, 'destination': rq.get('origin')}) 

            #Update the remaining capacity of storage 
            self.waterStored =  self.waterRemaining 

            self.waterStored_value.append(self.waterStored) # Graph values
            self.totaltime_value.append(self.total_time) # Simulation time 

            self.state = "respond" #Respond through conduit

        elif self.state == "idle" and respfromConduit != None :
            #response from conduit, with the needed amount of water, if avaialable/possible
            self.respfromConduit = respfromConduit
            #self.supply['quantity'] = self.waterToReq + self.respfromConduit[0][0].get('quantity') #Update water quantity


            self.supply['quantity'] = self.waterToDispatch + self.respfromConduit[0][0].get('quantity') # Amount to be sent to dispatcher
            self.supply_value.append(self.supply['quantity']) # Graph values

            self.waterNeedTot = 0 #Re-initialize 
            self.state = "send"
            
        else:
            print ("ERROR in STORAGE model EXTERNAL TRANSITION FUNCTION, ZONE : __ %s", self.zone) 
        return self.state 
        
    def intTransition(self):
    #Internal Transition Function, defining state change internally
        self.total_time += self.timeAdvance()
                    
        if self.state == "store" or self.state == "retrieve" :
            self.state = "idle"

        elif self.state == "request" or self.state == "respond" or self.state == "send":
            self.state = "idle" 

        else:
            print ("ERROR in STORAGE Atomic model INTERNAL TRANSITION FUNCTION")
        return self.state


    def outputFnc(self):
    # Output Funtion, specifying the output to send to the dispatcher     

        if self.state == "request":

            # Send request through conduit 
            return {self.ReqToConduit: [copy.copy(self.supply)]} 

        elif self.state == "respond":
            # Send response through conduit
            return {self.RespToConduit: [copy.copy(self.waterToShare)]} 

        elif self.state == "send":
            #Water delivered to dispatcher
            return {self.WaterDelivered: [copy.copy(self.supply)]} 

        else:
            return {}
            
            
    def timeAdvance(self):
    # Time advanse function
        if self.state == "store"  or self.state == "retrieve" or self.state == "respond" or self.state == "request" or self.state == "send":   
            return 0
        elif self.state == "idle" or self.state == "wait":  
            return INFINITY 
        else:
            raise DEVSException(\
                "unknown state <%s> in STORAGE Atomic model ADVANCE FUNCTION"\
                % self.state)






