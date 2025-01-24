#This model builds a electricity system, including loads, dispatcher 
#unit commitment and generators. 

import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy
import os

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import Simulator

from WaterStorageModel import WaterStorage 
from WaterDemandModel import WaterDemand
from WaterDispatchModel import WaterDispatch 
from WaterSourceModel import WaterSource
from PowerDispatchModel import  PowerDispatch
from PowerDemandModel import  PowerDemand
from PowerSourceModel import  PowerSource
from PumpReqModel import  PumpReq
from WaterCanalModel import WaterCanal
from WaterTransferModel import TransmissionConduit
from Functions import *


#This class represents the coupling of all models constituting the water-power system
class WaterSystem(CoupledDEVS):
	def __init__(self, name=None):
		CoupledDEVS.__init__(self, name)
		
		self.name = name	
		
		#File path 
		file_path = r'C:/Users/TOBAD/OneDrive - Idaho National Laboratory/INL_PROJECTS/WPTO Projects/FY21/Model_LatestVersion'


		# Read document 
		waterdmd = file_path + r'/Data/waterDemand.csv'
		watersupply = file_path + r"/Data/waterSupply.csv"
		powersupply = file_path + r"/Data/powerSupply.csv"
		powerdmd = file_path + r"/Data/powerDemand.csv"
		waterpump = file_path + r"/Data/waterPump.csv"
		canal = file_path + r'/Data/waterCanal.csv'
		storage = file_path + r"/Data/storageSupply.csv"
		conduit = file_path + r"/Data/transConduit.csv"
		zone = file_path + r"/Data/zoneLocation.csv"

		#Create instances of water Dispatcher
		self.waterdispatch = self.addSubModel(WaterDispatch(name = "watDis_" + self.name, zone = self.name))

		#Create instances of power Dispatcher
		self.powerdispatch = self.addSubModel(PowerDispatch(name = "powDis_" + self.name, zone = self.name))
		# link between power and water dispatchers
		self.connectPorts(self.powerdispatch.SupplyToWater, self.waterdispatch.AvailablePower)

		
		# Create instances of water canals
		self.watercanals = []
		for i in readCanal(canal):
			self.watercanal = self.addSubModel(WaterCanal(name = i.get('name'), origin = i.get('origin'), destination = i.get('destination'), 
                                                               flow = i.get('flow'), zone = i.get('region'), loss_pump = i.get('loss_pump'), loss_irrig = i.get('loss_irrig') ))
			self.connectPorts(self.watercanal.WaterDelivered, self.waterdispatch.AvailableWater)
			self.connectPorts(self.waterdispatch.SupplyToCanal , self.watercanal.WaterUtilized)
			#List of canals 
			self.watercanals.append(self.watercanal)
			
		# Create instances of water source/ main reservoir 
		for i in readSource(watersupply):
			self.watersource = self.addSubModel(WaterSource(name= i.get('name'), zone = i.get('zone')))
			for canals in self.watercanals:
				self.connectPorts(self.watersource.WaterDelivered, canals.WaterReceived)
				self.connectPorts(canals.WaterRequested, self.watersource.WaterRequestReceived)

		# Create instances of water demand
		for i in readWaterDemand(waterdmd):
			#print (i)
			self.waterdemand = self.addSubModel(WaterDemand(name = i.get('name'), canal = i.get('canal'), zone = i.get('zone')))
			self.connectPorts(self.waterdispatch.SupplyToDemand, self.waterdemand.WaterSupplied)
			self.connectPorts(self.waterdemand.WaterDemand, self.waterdispatch.DemandForWater)
			
		# Create instances of power source
		for i in readSource(powersupply):
			self.powersource = self.addSubModel(PowerSource(zone = i.get('location'), name = i.get('name')))  
			self.connectPorts(self.powersource.PowerToDeliver, self.powerdispatch.AvailablePower)
			self.connectPorts(self.powerdispatch.SupplyToSource, self.powersource.PowerSupplyUsed)
		
		# Create instances of power demand
		for i in readPowerDemand(powerdmd):
			self.powerdemand = self.addSubModel(PowerDemand(zone = i)) 
			self.connectPorts(self.powerdispatch.SupplyToDemand, self.powerdemand.PowerSupplied)
			self.connectPorts(self.powerdemand.PowerDemand, self.powerdispatch.DemandForPower)

		# Create instances of water pumps
		self.locations = []
		for i in readPump(waterpump):
			self.pumpreq = self.addSubModel(PumpReq(name = i.get('name'), zone = i.get('zone'), outage = i.get('outage'), canal = i.get('canal')))
			self.connectPorts(self.pumpreq.EnergyRequirement, self.powerdispatch.DemandForWater)
			self.connectPorts(self.powerdispatch.SupplyToPump, self.pumpreq.EnergySupplied)

		# Create instances of water storage
		self.waterstorages = []
		for i in readStorage(storage):
			self.waterstorage = self.addSubModel(WaterStorage(name = i.get('name'), zone = i.get('zone'), capacity = i.get('capacity'),
																 inflow = i.get('inflow'), outflow = i.get('outflow'), quantity = i.get('quantity')))
			# List of all storages in the area
			self.waterstorages.append(self.waterstorage)

			self.connectPorts(self.waterstorage.WaterDelivered, self.waterdispatch.WaterFromStorage)
			self.connectPorts(self.waterdispatch.RequestToStorage, self.waterstorage.ReqforWater)


		#Create instances of transmission conduints between storage 
		for wc in getWatConduit(conduit):
            # Create water transmission conduits
			self.waterconduit = self.addSubModel(TransmissionConduit(name= wc.get('name'), capacity = wc.get('capacity'), 
            					origin = wc.get('origin'), destination = wc.get('destination')))

            #Connect the differents storages via transmission conduits 
			self.connectPorts([x for x in self.waterstorages if x.zone == wc.get('origin')][0].ReqToConduit, self.waterconduit.RequestFromStorage) 
			self.connectPorts(self.waterconduit.RequestToStorage, [x for x in self.waterstorages if x.zone == wc.get('destination')][0].ReqfromConduit) 
			self.connectPorts([x for x in self.waterstorages if x.zone == wc.get('destination')][0].RespToConduit, self.waterconduit.ResponseFromStorage) 
			self.connectPorts(self.waterconduit.ResponseToStorage, [x for x in self.waterstorages if x.zone == wc.get('origin')][0].RespfromConduit)