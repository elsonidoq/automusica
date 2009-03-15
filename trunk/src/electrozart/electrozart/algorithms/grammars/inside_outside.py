from collections import defaultdict

def inside_outside(parser, corpus, niters):
    """
    params:
      parser :: nltk.AbstractParser
      corpus :: [string]
      niters :: int

    returns:
      h :: nltk.WeightedGrammar
    """
    sentence_freq= defaultdict(lambda :0)
    for sentence in corpus:
        sentence_freq[sentence]+= 1
    sentence_freq= sentence_freq.items()        

    sentence_trees= [None]*len(sentence_freq)
    for i, (sentence, freq) in enumerate(sentence_freq):
        sentence_trees[i]= list(parser.iter_parse(sentence))

    # ahora tengo dos gramaticas probabilisticas
    # old_pg y new_pg, construyo new_pg a partir de old_pg
    g= parser.grammar()
    prods_prob= uniform_prods(g)

    for it_no in xrange(niters):
        trees_freq=[None]*len(sentence_trees)
        # expectation step
        for i, sentence in enumerate(corpus):
            tree_probs=[None]*len(sentence_trees[i])
            for j, t in enumerate(sentence_trees[i]):
                tree_probs[j]= get_tree_prob(t, prods_prob)

            sentence_prob= sum(tree_probs)
            # uso tree_probs para meter la info del nuevo trees_freq
            for j, tree_prob in enumerate(tree_probs):
                tree_probs[j]= sentence_freq[i][1]*tree_prob/sentence_prob
            
            trees_freq[i]= tree_probs
        
        # maximization step
        prod_freq= defaultdict(lambda :0)
        # total de prod_freq por cada nonterminal
        nonterminal_total= defaultdict(lambda :0)
        for i, trees in enumerate(sentence_trees):
            for j, t in enumerate(trees):
                for prod in t.productions():
                    prod_freq[prod]+= trees_freq[i][j] 
                    nonterminal_total[prod.lhs().symbol()]+= trees_freq[i][j]  

        new_prods_prob= {}
        for prod, freq in prod_freq.iteritems():
            new_prods_prob[prod]= freq/nonterminal_total[prod.lhs().symbol()]

        prods_prob= new_prods_prob
        

    # creo la gramatica
    wprods= [None]*len(g.productions())
    for i, prod in enumerate(g.productions()):
        wprods[i]= WeightedProduction(prod.lhs(), prod.rhs(), prob=prods_prob.get(prod, 0))

    return WeightedGrammar(g.start(), wprods)
        
            
def get_tree_prob(tree, prods_prob):
    res= 1
    for prod in tree.productions():
        res*= prods_prob[prod] 
    return res        

    

from itertools import groupby
from nltk import WeightedProduction, WeightedGrammar
def uniform_prods(g):
    prods= g.productions()
    prods.sort(key=lambda x:x.lhs().symbol())
    prods_prob= {}
    for symbol, fragment in groupby(prods, key=lambda x:x.lhs().symbol()):
        fragment= list(fragment)
        assert len(set(prod.lhs().symbol() for prod in fragment)) == 1
        prob= 1.0/len(fragment)
        for prod in fragment:
            prods_prob[prod]= prob

    return prods_prob


