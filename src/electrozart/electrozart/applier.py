from parsing import ScoreParser 
from writing import ScoreWriter
from algorithms import TrainAlgorithm

class Applier(object):
    def __init__(self, parser_class, writer_class, 
                *algorithms):
        assert issubclass(parser_class, ScoreParser)
        assert issubclass(writer_class, ScoreWriter)

        for alg in algorithms: assert isinstance(alg, TrainAlgorithm)

        if len(algorithms) > 0:
            assert issubclass(algorithms[0].input_type, list)
            assert issubclass(algorithms[-1].output_type, Score)


        if len(algorithms) > 1:
            for prev, next in zip(algorithms, algorithms[1:]):
                assert issubclass(next.input_type, prev.output_type)

        self.parser_class= parser_class                
        self.writer_class= writer_class                
        self.algorithms= algorithms

    def apply(self, fnames, parserkwargs, outfname):
        parser= self.parser_class(**parserkwargs)
        scores= [parser.parse(fname) for fname in fnames]
        res= scores

        for alg in self.algorithms:
            res= alg.apply(res)
            
        writer= self.writer_class()
        writer.dump(res, outfname)
        return res            
