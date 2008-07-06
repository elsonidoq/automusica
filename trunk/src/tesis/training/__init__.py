from tesis.freedots import musicxml
from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from tesis.hmm.hidden_markov_model import MeanHiddenMarkovModel
from tesis.hmm.random_variable import ConstantRandomVariable
from itertools import imap

def train_hmm(fnames, score2obs_seq):
	learner= HiddenMarkovLearner()
	hidden_states= set()
	for i, fname in enumerate(fnames):
		print "loading", fname
		score= musicxml.load_file(fname)

		print "\tconverting to observation seq"
		obs_seq= score2obs_seq(score)

		hidden_states.update(imap(lambda x:x[0], obs_seq))

		print "\ttraining model"
		learner.train(obs_seq)

	initial_probability= dict( ((s,1.0/len(hidden_states)) for s in hidden_states) )
	print "building result"
	return learner.get_trainned_model(initial_probability)
	return models
	return MeanHiddenMarkovModel(models)



def simple_score2oseq(score):
	"""
	transforma una partitura en una secuencia de notas. 
	Los hidden states no representan nada mas que el tic
	en el que ocurre
	nombres que dependen 
	"""
	tic_number= 1
	res= []
	for part in score.parts:
		for measure in part.measures:
			for note in measure.musicdata.justNotes():
				tic_number+= 1
				var= ConstantRandomVariable(note, 'note')
				res.append((tic_number, {var:note}))



	return res
