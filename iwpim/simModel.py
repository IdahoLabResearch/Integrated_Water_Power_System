# "Copyright 2025, Battelle Energy Alliance, LLC All Rights Reserved"

from __future__ import division
from operator import *
import statistics
import sys
import csv


# Import code for model simulation:
from pypdevs.simulator import Simulator
import matplotlib.pyplot as plt
import numpy as np
import pylab 
import time 
import random

# Import the model to be simulated
from InterWaterSystemModel import InterWaterSystem
from Functions import *




#================================================================
start = time.perf_counter()
print ("The simulation staRTS ")
random.seed(a=5)
#Call the feedBD function

#    ======================================================================

# 1. Instantiate the (Coupled or Atomic) DEVS at the root of the 
#  hierarchical model. This effectively instantiates the whole model 
#  thanks to the recursion in the DEVS model constructors (__init__).
interWaterSystem = InterWaterSystem(name="interWaterSystem")

# 2. Link the model to a DEVS Simulator: 
#  i.e., create an instance of the 'Simulator' class,
#  using the model as a parameter.
sim = Simulator(interWaterSystem)

#    ======================================================================

# 3. Perform all necessary configurations, the most commonly used are:

#  A. A termination condition is prefered over a termination time,
runLength = 50
def termFunc(clock, interWaterSystem): 
	if clock[0] > runLength:
		# Or if the clock has progressed past simulation time 10
		print (['X' for i in range(10) ])
		return True
	else:
		a = 	(10*clock[0] )/runLength
		b = ['X' if i <= a else '-' for i in range(10) ]
		# Otherwise, we simply continue
		if random.random() > .99: print (b)
		return False

sim.setTerminationCondition(termFunc)

# B. Set the use of a tracer to show what happened during the simulation run
#    Both writing to stdout or file is possible:
#    pass None for stdout, or a filename for writing to that file
#sim.setVerbose(None)
sim.setVerbose('output.txt')

# C. Use Parallel DEVS instead of Classic DEVS
#    If your model uses Parrallel DEVS, this configuration MUST be set as
#    otherwise errors are guaranteed to happen.

sim.setClassicDEVS(classicDEVS = False)

#    ======================================================================
# 4. Simulate the model
sim.simulate()

print ("The simulation lasts %s" %(time.perf_counter() - start))
#    ======================================================================

# 5. Graph

#Initialize  lists for output graph results 

















