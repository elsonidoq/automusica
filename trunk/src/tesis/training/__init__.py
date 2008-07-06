from tesis.freedots import musicxml
from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from tesis.hmm.hidden_markov_model import MeanHiddenMarkovModel
from tesis.hmm.random_variable import ConstantRandomVariable

def train_hmm(fnames, score2obs_seq):
	models= [None]*len(fnames)
	for i, fname in enumerate(fnames):
		print "loading", fname
		score= musicxml.load_file(fname)

		print "\tconverting to observation seq"
		obs_seq= score2obs_seq(score)

		hidden_states= map(lambda x:x[0], obs_seq)
		init_probs= dict( ((h,1.0/len(hidden_states)) for h in hidden_states) ) 

		print "\ttraining model"
		models[i]= HiddenMarkovLearner(obs_seq, init_probs).get_hidden_markov_model()

	print "building result"
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
