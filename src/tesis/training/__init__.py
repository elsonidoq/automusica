from tesis.freedots import musicxml
from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from tesis.hmm.hidden_markov_model import MeanHiddenMarkovModel

def train_hmm(fnames, score2obs_seq):
	models= [None]*len(fnames)
	for i, fname in enumerate(fnames):
		score= musicxml.load_score(fname)

		obs_seq= score2obs_seq(score)

		hidden_states= map(lambda x:x[0], obs_seq)
		init_probs= dict(((h,1.0/len(hidden_states) for h in hidden_states)))

		models[i]= HiddenMarkovLearner(obs_seq, init_probs).get_hidden_markov_model()

	return MeanHiddenMarkovModel(models)


