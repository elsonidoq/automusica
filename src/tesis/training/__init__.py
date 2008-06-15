from tesis.freedots import musicxml
from tesis.hmm import hidden_markov_learner

def train_hmm(fnames, score2obs_seq):
	for fname in fnames:
		score= musicxml.load_score(fname)
		obs_seq= score2obs_seq(score)

