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
from itertools import groupby
import random
from pypdevs.simulator import Simulator
import matplotlib.pyplot as plt
import numpy as np
import pylab 
import datetime




class WaterDispatch(AtomicDEVS):
    def __init__(self, name=None, zone = None):

        AtomicDEVS.__init__(self, name)
        self.state = "idle"
        self.elapsed = 0
            
        #Initialization of all variables in the class "Dispatcher"
        self.name = name #Name of the dispatcher
        self.zone = zone #zone of the dispatcher
        
        self.elapsed = 0
        self.total_time = 0	#Total simulation time

        self.demandToBeMet = {} #Different types of demmand
        self.availableCapacity = {} #Available Capacity per generator
        self.TotalAvailableCapacity = 0 #Total power capacity, considering all generators combined 
        self.TotalDemand = 0 #Total demand, combining all loads requests
        self.demandMetNoPump_value = []            
        self.total_time_value = []
        self.demandMetPump_value = []
        self.TotalWaterUsed_value = []

        #Name of input/output ports used in this class
        self.DemandForWater = self.addInPort(name="DemandForWater") #Demand different types
        self.AvailableWater= self.addInPort(name="AvailableWater")  #Available water quantity from sources
        self.AvailablePower= self.addInPort(name="AvailablePower")  #Avaialable power quantity 
        self.WaterFromStorage= self.addInPort(name="WaterFromStorage") #Water from storage

        #Output port specifying the amount of demand met 
        self.SupplyToDemand = self.addOutPort(name="SupplyToDemand") #Supply to water demand
        self.SupplyToCanal = self.addOutPort(name="SupplyToCanal") #Supply to water canal
        self.RequestToStorage  = self.addOutPort(name="RequestToStorage") #Message sent to storage requesting water
    
    def extTransition(self, inputs):
	#External Transition Function
        self.total_time += self.elapsed #Update the total time for the simulation
                
        demandForWater = inputs.get(self.DemandForWater) #demand for water from customers
        availableWater = inputs.get(self.AvailableWater) #water from various sources 
        waterFromStorage = inputs.get(self.WaterFromStorage) #water from storage
        availablePower = inputs.get(self.AvailablePower) #proportion of power  needed to distribute water, from power dispatch - pumps input
        #waterOtherFromStorage = inputs.get(self.WaterOtherFromStorage) #proportion of power  needed to distribute water, from power dispatch - pumps input

        if self.state == "idle" and (demandForWater != None and availableWater != None):
            self.demandForWater = demandForWater 
            self.availableWater = availableWater


            self.TotalAvailableCapacity = 0
            self.TotalMet = 0
            self.TotalDemand = 0
            self.waterSurplus =[]
            self.demandMetNoPump = 0
            self.demandMetPump = 0
            self.TotalWaterUsed = []
            
            #compute the total amount of water avaialable ##############################
            for wat in self.availableWater: #water avaialable per canal 
                self.TotalAvailableCapacity += float(wat.get('supply')) # Add total supply 
                self.TotalAvailableCapacity -= float(wat.get('TotalLoss')) # update for loss 
            
            #compute the total amount of water demand ###################################
            self.TotalDemand = sum(dmd['quantity'] for dmd in self.demandForWater if dmd)
            
            #compute the eventual surplus for storage #################################
            #Surplus at the system level 
            self.waterSurplus = self.TotalAvailableCapacity - self.TotalDemand

            for dmd in self.demandForWater:
                self.PropDemand = "{:.2f}".format(dmd.get('quantity')/self.TotalDemand) #proportion water demand
                self.PropDemand = float(self.PropDemand)

                #update dictionary
                dmd.update({'proportion': self.PropDemand, 'surplus': self.waterSurplus})
            self.state = "tostorage" #If surplus of water
            

        #add excess of water if available to existing qty to meet demand
        elif self.state == "wait" and waterFromStorage != None :
            self.waterFromStorage = waterFromStorage

            for stg in self.waterFromStorage:
                #Sum up the avaialable water quantity and storage
                self.TotalAvailableCapacity += stg.get('quantity')  

            #compute potential water demand to be met
            self.WaterdemandToBeMet = DemandSupplyBalance(self.demandForWater, self.TotalAvailableCapacity)

            #####################################################################
            self.demandMetNoPump = self.TotalAvailableCapacity/self.TotalDemand
            self.demandMetNoPump_value.append(self.demandMetNoPump)
            self.total_time_value.append(self.total_time)
            ###################################################################
            self.state = "waitforpower" 


        #compute definitive demand met with power 
        #This input represents the amount of power for pumps, comimg from Power dispatch
        elif self.state == "waitforpower" and availablePower != None : 
            self.availablePower = availablePower
            
            #Make sure water demand is met, based on pump energy requirement
            for i in self.WaterdemandToBeMet: #water demand to be met 
                for j in availablePower[0]: 
                    if i.get('canal') == j.get('canal'): #water demand to be met on different canals
                        i['quantity'][0]= float(j.get('quantity')[1]) * float(i.get('quantity')[0])
                        self.TotalMet += i['quantity'][0] #Total water demand met 
                        self.TotalWaterUsed.append(self.TotalMet)
                        break 
            
            #Assess which canal has been used and for which quantity  ##########################################
            #Rank all water canal from highest to lowest supply(From most to less important demand) 
            self.WaterSourceRanking = RankWaterCanal(self.availableWater)
            # Water canal usage 
            self.SourceWaterUsed = CanalUsage(self.WaterSourceRanking, self.TotalMet)

            self.state = "respondToDemand" 	
                    
        else:
            print ("ERROR IN WATER DISPATCHER MODEL EXTERNAL TRANSITION FUNCTION") 
        return self.state 


    def intTransition(self):
    #Internal Transition Function
        self.total_time += self.timeAdvance()
        if self.state == "tostorage" or self.state == "request_again": 
            self.state = "wait"	
                
        elif self.state == "respondToDemand" : 
            self.state = "idle"

        else:
            print ("ERROR in water DISPATCHER Atomic model INTERNAL TRANSITION FUNCTION")
        return self.state   
                      
    def outputFnc(self):
    # Output Funtion.
        if self.state == "tostorage" : 	
            return {self.RequestToStorage: [copy.copy(self.demandForWater)]} 
                        
        elif self.state == "respondToDemand": 
            #Return the amount of demand met and power needed per generator  
            return {self.SupplyToDemand: [copy.copy(self.WaterdemandToBeMet)], self.SupplyToCanal: [copy.copy(self.SourceWaterUsed)] }
        else:
            return {}
                    
            
    def timeAdvance(self):
    # Time advanse function
        
        if self.state == "idle" or self.state == "wait" or self.state == "waitforpower":
            return INFINITY 
        elif self.state == "respondToDemand" or self.state == "tostorage" :
            return 0
        else:
            raise DEVSException(\
                "unknown state <%s> in DISPATCHER Atomic model ADVANCE FUNCTION "\
                % self.state) 
                
