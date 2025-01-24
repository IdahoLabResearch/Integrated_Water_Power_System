#Set of all functions used in the simulation model
import sys
import copy
import matplotlib.pyplot as plt
from operator import add
import time
from scipy.stats import weibull_min
import random 
import os
import csv
import pandas as pd 
from itertools import *

file_path = r'C:/...'

# Read document 
waterdmd = file_path + r'/Data/waterDemand.csv'
watersupply = file_path + r"/Data/waterSupply.csv"
powersupply = file_path + r"/Data/powerSupply.csv"
powerdmd = file_path + r"/Data/powerDemand.csv"
waterpump = file_path + r"/Data/waterPump.csv"
canal = file_path + r'/Data/waterCanal.csv'
storage = file_path + r"/Data/storageSupply.csv"
conduit = file_path + r"/Data/transConduit.csv"
hydro = file_path + r"/Data/hydroFlow.csv"
solar = file_path + r"/Data/solarData.csv"
wind = file_path + r"/Data/windData.csv"

def readWaterDemand(fname): #Function to read water demand from database
	listDemand = []
	count = 0
	demand = []
	listDemandList  = []	
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			if count < 2:
				count += 1
			else:				
				listDemand.append ({"name": row[2], "demand": row[3:], "canal": row[0], "zone": row[1]}) 
	for lst in listDemand:
		for elt in lst.get('demand'):
			elt = float (elt)
			demand.append(float(elt))
		lst['demand'] = demand 
		demand =[]
		listDemandList.append(lst)
	return listDemandList 

def aggregateWaterDemand(fname): #Function to aggregate water demand per canal
	waterDemandCanal = []
	canaldmd =[]
	list_canaldmd = []
	aggr_canaldmd =[]
	dict_canaldmd = []
	waterDemand = readWaterDemand(waterdmd)
	waterDemand = sorted(waterDemand, key = key_func)

	#Group water demand per canal
	for key, value in groupby(waterDemand, key_func):
		waterDemandCanal.append(list(value)) 

	# Aggregate all demand from the same canal
	for wtrDemand in waterDemandCanal:
		for wtrdmd in wtrDemand:
			aggr_canaldmd.append(wtrdmd.get('demand'))
		# Several farms on the same canal 
		if len(aggr_canaldmd) >=2: 
			canaldmd = [sum(dmd) for dmd in zip(*aggr_canaldmd)] # Demand on each canal
			dict_canaldmd.append({'canal': wtrdmd.get('canal'), 'demand': canaldmd})
		# Single farm on canal 
		else:
			canaldmd = wtrdmd.get('demand') 
			dict_canaldmd.append({'canal': wtrdmd.get('canal'), 'demand': canaldmd})
		list_canaldmd.append(canaldmd)
		aggr_canaldmd = [] # Re-initialize so it won't aggregate
	return dict_canaldmd

def irrgMod (fname):
	impMethod = {}
	count = 0
	demand = [] 
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			if count < 1:
				count += 1
			else:				
				impMethod.update ({row[0]: row[1]})
	return impMethod

def readPowerDemand(fname): #Function to read power demand from database
	listDemand = {}
	listDemandList = []
	count = 0
	demand = [] 
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			if count < 2:
				count += 1
			else:				
				listDemand.update ({row[0]: row[1:]}) 
	for i in listDemand:
		for j in listDemand[i]: #i.get('demand'):
			demand.append(float(j))	#To convert list element to float
			listDemand.update({i: demand})	#To convert list element to float
		demand = [] 
	return listDemand 

def readSource(fname): #Function to read power source from database
	count = 0
	source  = []
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			i = 0
			for r in row:
				i +=1
				if "Loc" in r:
					break 
			source.append ({"name":row[0], "location": row[i-1]}) 	
		del source[0]		
	return source

def readPump(fname): #Function to read pump list and energy requirements from database
	count = 0
	source  = []
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			source.append ({"name":row[0], "zone": row[1], "quantity": row[2], "outage": row[4], "canal": row[3]}) 	
		del source[0]		
	return source

def readStorage(fname): #Function to read water storage  from database
	count = 0
	source  = []
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			source.append ({"name":row[0], "zone": row[2], "capacity": row[1], "inflow": row[3], "outflow": row[4], "quantity": row[5]}) 	
		del source[0]		
	return source

def getZones(fname):
	zones  = []
	count = 0
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			if count < 2:
				count += 1
			else:				
				#zones.append ({"name":row[0]}) 	
				zones.append (row[0]) 	
	return zones

def getWatConduit(fname): #Function to read water canal from database	
	watCdt  = []
	count = 0
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:	
			watCdt.append ({"origin":row[1],"destination":row[2],"capacity":row[3], "name":row[0]})
		del  watCdt[0]
	return watCdt

	
def readCanal(fname): #Function to read water canal from database
	count = 0
	canal  = []
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			canal.append ({"name":row[0], "origin": row[1], "destination": row[2], "region" : row[3], "flow": row[4], "loss_pump": row[5], "loss_irrig": row[6]}) 	
		del canal[0]		
	return canal
	
def readDataSeries(fname): #Read data over time 
	listFlow = {}
	count = 0
	flow = [] 
	with open(fname) as f:
		csvFile = csv.reader(f, delimiter=",")
		for row in csvFile:
			if count < 2:
				count += 1
			else:				
				listFlow.update ({row[0]: row[1:]}) 
	for i in listFlow:
		for j in listFlow[i]:
			flow.append(float(j))	
			listFlow.update ({i: flow}) 
	return flow


def getHydroPower(sourceName): #Compute the power from hydro 
	head = 74 #in ft
	efficiency = 0.7
	flow = readDataSeries(hydro)
	#hydro = [efficiency * head * x /11.800 for x in flow]
	#hydro = [random.uniform (1, 1.0) * x for x in hydro]
	hydroPower = [random.uniform (1, 1.0) * x for x in flow] #power generated from hydro
	#print ("power generated--------------------", hydro)
	return hydroPower 
	#ratio = #95 L of water to produce 1 kilowatt-hour
	#source: https://spectrum.ieee.org/energy/environment/how-much-water-does-it-take-to-make-electricity
	#source: https://www.slideshare.net/GhassanHadi/u3-l1introtohydroelectricpower
	
def getSolarPower(sourceName): #Compute the power from solar 
	area = 20
	efficiency = 0.46
	tempCoeff = 0.1
	#compute the power , based on the radiations and the area considered
	power = [area * x for x in readDataSeries(solar)]
	#Compute the gain or loss in efficiency, based on the temperture 
	new_temp = [77 - x  for x in readDataSeries("temperatureData.csv")] #77F is the refeence temperature 
	tempLoss = 	[tempCoeff * i for i in new_temp]
	LossOrGainCoeff = [p*t for p,t in zip(power, tempLoss)]
	LossOrGain = []
	for lg,p in zip(LossOrGainCoeff, power):
		if p == 0:
			L_G = 0
		else:
			L_G = lg/p 
		LossOrGain.append(L_G)
	#Compute the capacity 
	return [(1+l) * p *  efficiency * 0.1  for l,p in zip(LossOrGain, power) ]   #Need for documentation and Unit conversion 

def getWindPower(sourceName): #Compute the power from wind 
	Vcutin = 5 #Minimum operating wind speed
	Vcutoff = 25 #Speed at which the wind power is shut off 
	Prated = PowerSourceCapacity(sourceName) #Maximum power capacity
	Vrated = 20 #Speed at which the maximm capacity is reached
	wspeed = readDataSeries(wind)
		
	#Determine the parameters of the Weibul (scale and shape) 
	shape, loc, scale = weibull_min.fit(wspeed, floc=0)
	#scale = 15
	#shape = 2
	wspeedGenerated =(weibull_min.rvs(c = shape, loc=loc, scale=scale, size= 24))
	#print "WIND SPEED FROM WEIBULL %s" %wspeedGenerated		
	xlist = []
	for j in wspeedGenerated:
		if j < Vcutin or j > Vcutoff:
			powerOutput = 0
		elif j <= Vcutoff and j >= Vrated:
			powerOutput = Prated
		elif j >  Vcutin and j < Vrated:
			powerOutput = Prated * ((j - Vcutin)/(Vrated - Vcutin))**2
		else:
			print ("OUT OF RANGE")
		xlist.append(powerOutput)
	return [random.uniform (1, 1.0) * x for x in xlist]


# def EnergySourceUsage(EnergySource, TotalDemand): #Compute the power generation source usage
# 	EnergySourceUsed = []
# 	SourcesAscendByCost = sorted(EnergySource, key=lambda k: k['cost']) 
# 	for source in SourcesAscendByCost:
# 		TotalDemand -= source.get('quantity')
# 		if TotalDemand >= 0:
# 			quantityUsed = source.get('quantity')
# 		else:
# 			quantityUsed = TotalDemand + source.get('quantity')
# 			TotalDemand = 0
# 			if quantityUsed < 0:
# 				quantityUsed = 0
# 		EnergySourceUsed.append({'name': source.get('name'), 'quantity': quantityUsed, 'cost': source.get('cost'), 'technology': source.get('technology')})
# 	return EnergySourceUsed
	 

def replenishCapacity(source, capacity): #Function to replenish water in canal when below threshold  
	Q =  WaterFlow (source.get('name'))#Flow through the pipe (acre foot /hr)
	currentCapacity = source.get ('capacity') 
	currentCapacity += Q
	if currentCapacity < capacity:
		currentQuantity = currentCapacity 
	else: 
		currentQuantity = capacity 
	source.update({'capacity': currentQuantity}) 
	return source.get ('capacity')
	
# Following functions to read various factors #####33
def getHydroHead ():
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency', 'Cost'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc["Head"]) 

def getHydroEfficiency (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency', 'Cost', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Efficiency"]) 

def WaterSourceCapacity (sourceName):
	df = pd.read_csv(watersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Capacity"])

def PowerSourceCapacity (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Capacity"]) 
	
def StorageSourceCapacity (sourceName):
	df = pd.read_csv(storage, usecols = ['Source', 'Capacity', 'Location','Inflow', 'Outflow'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Capacity"])

def StorageSourceOutflow (sourceName):
	df = pd.read_csv(storage, usecols = ['Source', 'Capacity', 'Location','Inflow', 'Outflow'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Outflow"])

def StorageSourceInflow (sourceName):
	df = pd.read_csv(storage, usecols = ['Source', 'Capacity', 'Location','Inflow', 'Outflow'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Inflow"])

def StorageSourceQuantity (sourceName):
	df = pd.read_csv(storage, usecols = ['Source', 'Capacity', 'Location','Inflow', 'Outflow', 'Quantity'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Quantity"])


def WaterForIrrigation (sourceName):
	df = pd.read_csv(watersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Irrigation"]) 

def WaterForPower (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Category', 'Capacity', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency', 'Power', 'Cost'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Power"]) 

def WaterFlow (sourceName):
	df = pd.read_csv(watersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"ReplenishFlow"]) 

def WaterCapacityThreshold (sourceName):
	df = pd.read_csv(watersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Threshold"])


def PowerCapacityThreshold (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Irrigation', 'Power'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Threshold"]) 

def getDamHead (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Head"])

def getDamEfficiency (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Efficiency"])  

def getSupplyType (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Category"])

def getPumpInfo (sourceName):
	df = pd.read_csv(waterpump, usecols = ['Pump', 'Power', 'Location'])
	df2 = df.set_index("Pump", drop = False)
	return (df2.loc[sourceName,"Location"])

def getRegion ():
	df = pd.read_csv(storage, usecols = ['Location'])
	df2 = df.set_index("Location", drop = False)
	return (df2.loc["Location"])
    
   
def getCost (sourceName):
	df = pd.read_csv(powersupply, usecols = ['Source', 'Capacity', 'Category', 'Threshold', 'ReplenishFlow', 'Head', 'Efficiency', 'Cost'])
	df2 = df.set_index("Source", drop = False)
	return (df2.loc[sourceName,"Cost"])
############################################################################# 


def WaterUse(waterToStore, capacity, waterStored, inflow, outflow): #Compute the water usage from storage 
	waterToShare = 0
	if waterToStore >= 0:
		#water available to store
		if inflow >= waterToStore: #Ensuring the inflow constraint is respected
			waterStored += waterToStore
		else:
			waterStored += inflow
		if waterStored > capacity:
			waterStored = capacity	
		waterToShare = 0 #No water is taken out of the storage 
	else: #no excess water, rather water is needed
		if waterStored == 0:
			waterToShare = waterToStore
			waterToStore = 0
		else:
			if abs(waterToStore)<= outflow: 
				waterToShare = abs(waterToStore)
			else:
				waterToShare = outflow
			waterStored -= waterToShare

			if waterStored < 0:
				waterStored += waterToShare
				#print ("YES")
				waterToShare =  waterToStore + abs(waterStored)
				waterStored = 0

	return [waterToShare, waterStored]
	
	
def RetrievePower (waterStored, waterNeeded):
	waterToShare = 0
	if waterStored > waterNeeded:
		waterToShare = waterNeeded
	else:
		waterToShare = waterStored
	return waterToShare  

def RankWaterCanal (CanalSources):
	SourcesAscendByCost = sorted(CanalSources, key=lambda k: k['supply']) 
	return SourcesAscendByCost 

def RankEnergySources (EnergySources):
	SourcesAscendByCost = sorted(EnergySources, key=lambda k: k['cost']) 
	return SourcesAscendByCost 


DemandType = []
def DemandSupplyBalance(Demand, PowerAvailable): #Function to distribute water supply to meet demand 
	DemandType = []
	for i in Demand:
		PowerAvailable -= float(i.get('quantity'))
		if PowerAvailable >= 0:
			DemandMet = float(i.get('quantity'))
		else:
			DemandMet = PowerAvailable + float(i.get('quantity'))
			PowerAvailable = 0
			if DemandMet < 0:
				DemandMet = 0
		DemandType.append({'name':i.get('name'), 'canal': i.get('canal'), 'quantity':[DemandMet, float(DemandMet/float(i.get('quantity')))]})
	return DemandType

DemandType = []
def PowerSupplyBalance(Demand, PowerAvailable): #Function to distribute power supply to meet demand
	DemandType = []
	for i in Demand:
		PowerAvailable -= float(i.get('quantity'))
		if PowerAvailable >= 0:
			DemandMet = float(i.get('quantity'))
		else:
			DemandMet = PowerAvailable + float(i.get('quantity'))
			PowerAvailable = 0
			if DemandMet < 0:
				DemandMet = 0
		DemandType.append({'name':i.get('zone'), 'quantity':[DemandMet, float(DemandMet/float(i.get('quantity')))]})
	return DemandType


DemandType = []
def DemandSupply(Demand, PowerAvailable): #Function specifying the amount of demand that is covered   
	DemandType = []
	#for i in Demand:
	#print ('function used -------------', Demand)
	#for i in Demand:
	PowerAvailable -= float(Demand.get('quantity'))
	if PowerAvailable >= 0:
		DemandMet = float(Demand.get('quantity'))
	else:
		DemandMet = PowerAvailable + float(Demand.get('quantity'))
		PowerAvailable = 0
		if DemandMet < 0:
			DemandMet = 0
	if Demand.get('quantity') == 0:
		DemandType =({'canal':Demand.get('canal'),'name':Demand.get('name'), 'quantity':[DemandMet, 1] , 'canal':Demand.get('canal')})
	else: 
		DemandType =({'canal':Demand.get('canal'), 'name':Demand.get('name'), 'quantity':[DemandMet, float(DemandMet/float(Demand.get('quantity')))] , 'zone':Demand.get('zone')})
	return DemandType


DemandType = []
def DemandSupply_Outage(Demand, PowerAvailable): #When there is no pump, but it is no outage 
	DemandType = []
	#for i in Demand:
	DemandType = ({'canal':Demand.get('canal'),'name':Demand.get('name'), 'quantity':[0, 0], 'zone':Demand.get('zone')})
	return DemandType
	
def EnergySourceUsage(EnergySource, TotalDemand): #Compute the power generation source usage
	EnergySourceUsed = []
	TotalEnergyUsed = 0
	for source in EnergySource:
		TotalDemand -= source.get('quantity')
		if TotalDemand >= 0:
			quantityUsed = source.get('quantity')
		else:
			quantityUsed = TotalDemand + source.get('quantity')
			TotalDemand = 0
			if quantityUsed < 0:
				quantityUsed = 0
		EnergySourceUsed.append({'name': source.get('name'), 'quantity': quantityUsed, 'cost': source.get('cost'), 'technology': source.get('technology')})
		TotalEnergyUsed += quantityUsed
	return [EnergySourceUsed, TotalEnergyUsed]


def CanalUsage(CanalSource, TotalDemand): #Compute the canal usage
	WaterSourceUsed = []
	TotalWaterUsed = 0
	for source in CanalSource:
		TotalDemand -= source.get('supply')
		if TotalDemand >= 0:
			quantityUsed = source.get('supply')
		else:
			quantityUsed = TotalDemand + source.get('supply')
			TotalDemand = 0
			if quantityUsed < 0:
				quantityUsed = 0
		WaterSourceUsed.append({'name': source.get('name'), 'quantity': quantityUsed})
		TotalWaterUsed += quantityUsed
	return [WaterSourceUsed, TotalWaterUsed]
	

#Specify the remaining capacity after usage, on an hourly basis 
#Return a value		
def UpdateCapacity(a, b):
	return a - b


#Specify the energy lost caused by the transmission of power  
#Return a value	
def EnergyTransmission(request, loss, capacity):
	return min (request*(1+loss), capacity)

# Categorize demand per region for storage use.
def key_func(k):
    return k['canal']
    
def key_func1(k):
    return k['location']
