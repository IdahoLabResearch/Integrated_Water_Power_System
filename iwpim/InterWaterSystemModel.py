import sys
import copy
from operator import itemgetter
import collections
from collections import Counter
from copy import deepcopy

from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator
import csv
import matplotlib.pyplot as plt
import numpy as np
from Functions import *


from WaterSystemModel import WaterSystem
from WaterTransferModel import TransmissionConduit


class InterWaterSystem(CoupledDEVS):

       def __init__(self, name=None):
              CoupledDEVS.__init__(self, name)
              self.zone = self.addSubModel(WaterSystem(name= "IrrgSys"))


