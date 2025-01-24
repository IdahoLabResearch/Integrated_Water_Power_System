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
from Functions import *
from operator import add
import numpy as np
import pylab 

# Canals are supplied water from the main reservoir
#water in an irrigation reservoir may be released into networks of canals 
#for use in farmlands or secondary water systems

class WaterCanal(AtomicDEVS): 
    #Each water water canal is characterized by those parameters
    def __init__(self, name=None, origin = None, destination = None, flow = None, zone = None, loss_pump = None, loss_irrig = None): #Add characteristics of the generator
      
		# Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
		

  #Initialization of all variables of the class 
        self.state = "request" #initial state
        self.elapsed = 0             

        self.name = name #Name of the source
        self.origin = origin 
        self.destination = destination 
        self.zone = zone 
        self.flow = flow # Carrying capacity, or max flow of water circulatinf in the canal
        self.loss_pump = loss_pump # Loss through evaporation
        self.loss_pump =   float(self.loss_pump)
        self.loss_irrig =  loss_irrig
        self.loss_irrig =   float(self.loss_irrig)

        self.totalLoss = 0

		#Amount of water to supply 
        real = "waterCanal.csv"
        self.supply = {}
        self.supply['name'] = self.name
        self.supply['origin'] = self.origin
        self.supply['zone'] = self.zone
        self.supply['destination'] = self.destination
        self.supply['flow'] = float(self.flow) #Carrying capacity per time unit 
        self.flow = float(self.flow) #Carrying capacity per time unit 
        self.supply['supply'] = 0 # Amount of water supplied to Disp
        self.temp = 0 

        #Amount of water to request from source reservoir 
        self.rqst = 0  
        self.request = {}
        self.request['name'] = self.name
        self.request['destination'] = self.destination
        self.request['quantity'] = 0
		
        self.waterRequested = [] #Water planned to come out of the reservoir. It follows forecast demand
        self.waterRequestedCanal = 0 # Water to be sent to farms 

        self.TotalwaterUsed = 0 # total water used 

		#Get the forecast demand 		
        file_path = r'C:/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO PRojects/FY21/Model_LatestVersion'
        #file_path = r'/Users/tobad/Library/CloudStorage/OneDrive-IdahoNationalLaboratory/INL_PROJECTS/WPTO Projects/FY21/Model_LatestVersion'

        self.forecasted = file_path + r'/Data/waterForecastDemand.csv' #Data file for forecasted demand
        self.approach = file_path + r"/Data/irrgMod.csv"
        
        # Initialize irrigation modernization approach 
        #With pressurized pump, in lieu of canals, water is not lost to evaporation and seepage from canals. 
        if irrgMod (self.approach).get("Pressurized Pipe") == "NO": # No method implemented
            self.loss_pump =   self.loss_pump/180
        else:
            self.loss_pump = 0 # Method implemented

        #Spray irrigation loses about 35% of water applied due to evaporation and blowing winds
        if irrgMod (self.approach).get("Drip Irrigation") == "NO": # No method implemented
            self.loss_irrig =   self.loss_irrig
        else:
            self.loss_irrig = 0 # Method implemented
        #################################################################################################

        self.total_time = 0 #simulation time 
        #Graph variables --------------------------------------
        self.capacity_value = []
        self.totaltime_value = []
        self.waterUsed_value = []
        #-------------------------------------------------------
        
        #Input and output of the class ----------------------------------------------------------------------------------
        
        #Output messages sent by the agent 
        self.WaterRequested = self.addOutPort(name="WaterRequested") #Message sent to the main source indicating water needed 
        self.WaterDelivered = self.addOutPort(name="WaterDelivered") #Message sent to water dispatch 
        self.WaterReceived = self.addInPort(name="WaterReceived") #Message received from water source, from the same location (destination) 
        self.WaterUtilized = self.addInPort(name="WaterUtilized") #Message received water dispatch
        
		
    def extTransition(self, inputs):
    #External Transition Function, defining state change after receiving input from another class
        self.total_time += self.elapsed #Update the total time for the simulation
                
        waterReceived = inputs.get(self.WaterReceived) #Message received from water source, from the same location (destination) 
        waterUtilized = inputs.get(self.WaterUtilized) #Message received from water dispatch
        
        #Receive the amount of water from water source 
        if self.state == "wait" and waterReceived != None:
            self.waterReceived = waterReceived

            # Water received from reservoir 
            for wtr in self.waterReceived[0]:
                # Making sure the water requested goes to the  appropriate canal
                if self.name == wtr:
                    self.supply['flow'] += self.waterReceived[0][wtr]
            self.state = "supply"
        
        #Amount of water used from dispatch  
        elif self.state == "wait" and waterUtilized != None:
            self.waterUtilized = waterUtilized
            for wtr in self.waterUtilized[0][0]:
                # Make sure the correct canal is updated 
                if self.name == wtr.get('name'):
                    if  self.supply['supply'] == 0:
                        #proportion of water used
                        self.waterUsed = 0
                    else:
                        #proportion of water used
                        self.waterUsed = float(wtr.get('quantity'))/float(self.supply['supply'])

                    # Update the level of water, based on what was used 
                    self.supply['flow'] -= self.supply['supply'] * self.waterUsed
                    self.TotalwaterUsed += self.supply['supply'] * self.waterUsed

            
            # Graph variables 
            self.waterUsed_value.append(self.TotalwaterUsed)
            self.state = "advance"

        else:
            print ("ERROR in Water Canal Atomic model EXTERNAL TRANSITION FUNCTION")
        
        return self.state

			#Maybe add water quantity per canal 
		
    def intTransition(self):
    #Internal Transition Function, defining state change internally
        self.total_time += self.timeAdvance()
        
                    
        if self.state == "request":
            self.state = "wait"
        
        elif self.state == "supply":
            self.state = "wait"
        
        elif self.state == "advance":
            self.state = "request"

        else:		
            print ("ERROR in water cananl  Atomic model INTERNAL TRANSITION FUNCTION")
        return self.state

							
    def outputFnc(self):
    # Output Funtion, specifying the output to send to the dispatcher
        #Graph variables #######################################################
        
        ########################################################################
        k = 0
        if self.state == "request" :
            #Amount of water requested to source for each canal
            self.waterRequestedCanal = readWaterDemand(self.forecasted)  

            # Make sure the simulation time is incermenting by 1.
            k += 1 
            if self.total_time >= 2:
                self.total_time -= k
            
            self.supply['supply'] = 0
            self.request['quantity'] = 0
            self.totalLoss = 0
            self.temp = 0
            for wtrRqst in self.waterRequestedCanal:
                # Check if appropriate canal 
                if wtrRqst.get('canal') == self.name:
                    #If there is  enough water in the canal, we stop water flow upstream
                    if self.supply['flow'] > 0.8 * self.flow:
                        self.rqst = 0
                    
                    #If water in the canal goes below a certain threshold, then get water from upstream 
                    #The threshold here is 80% of the canal capacity  
                    else:
                        self.supply['flow'] <= 0.8 * self.flow
                        self.rqst = wtrRqst.get('demand')[int(self.total_time)%180] + self.flow * 0.2
                        #update canal water quantity 
                        self.supply['flow'] += self.flow * 0.2 - wtrRqst.get('demand')[int(self.total_time)%180]
                   
                    #Amount of water supplied to meet demand
                    self.supply['supply'] += wtrRqst.get('demand')[int(self.total_time)%180] 
                    
                    self.supply['supply'] = self.supply['supply'] + self.loss_pump #Water evap. per time unit
                    self.supply['supply'] = self.supply['supply'] * ( 1 + self.loss_irrig) #Water from spray
                    self.temp += self.supply['supply'] # Temporary value where quantity is stored, in order to track water losses 

                    self.totalLoss += self.loss_pump + self.supply['supply'] * self.loss_irrig/( 1 + self.loss_irrig) # Total additional water volume 

                    #Amount of water requested to source 
                    self.request['quantity'] += float (self.rqst)
                else:
                    #if no farms on canal, no request 
                    self.request['quantity'] += 0
                    self.supply['supply'] += 0
                
                self.supply['supply'] = self.temp #Pass on the value before re-initialization
                self.supply['supply'] = 0 
 

            return {self.WaterRequested: [copy.copy(self.request)]} 
        
        elif self.state == "supply" :
            #Level of water (to farms) sent to dispatcher 
            self.supply['TotalLoss'] = self.totalLoss
            self.supply['supply'] = self.temp
            return {self.WaterDelivered: [copy.copy(self.supply)]} 
        else:
            return {}
			
			
    def timeAdvance(self):
    # Time advanse function
        if self.state == "advance" :   
            return 1
        elif self.state == "supply" or self.state == "request" or self.state == "wait_1":  
            return 0
        elif self.state == "wait" :
            return INFINITY 			
        else:
            raise DEVSException(\
                "unknown state <%s> in water Atomic model ADVANCE FUNCTION"\
                % self.state)
                