#/usr/bin/python

from interval import *
from random_variable import *
from hidden_markov_model import *
from sys import argv
from hidden_markov_learner import *
from history_hidden_markov_model import *


eval("%s.test()" % argv[1])
	
