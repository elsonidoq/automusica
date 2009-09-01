
from sys import argv

from md5 import md5
import cPickle as pickle


from config import parserclass, modelclass, writerclass

from optparse import OptionParser
def main():
    usage= 'usage: %prog [options] infname [outfname]'
    parser= OptionParser(usage=usage)
    parser.add_option('-f', '--from', dest='moment_from', help='start moment in ticks', default=0)
    parser.add_option('-t', '--to', dest='moment_to', help='end moment in ticks')
    parser.add_option('-d', '--duration', dest='duration', help='duration of the slice')
    parser.add_option('-c', '--no-cache', dest='cache', action='store_false', default=True, help='discard cache')

    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')

    parser= parserclass('models_cache')
    moment_from= int(options.moment_from)
    if options.moment_to is None and options.duration is None:
        parser.error('falta --to y --duration')
    elif options.moment_to is None:
        moment_to= int(options.moment_from)+int(options.duration)
    else:
        moment_to= int(options.moment_to)

    infname= args[0]
    if len(args) == 1: outfname= '%s-%s-%s.mid' % (infname[:-4], moment_from, moment_to)
    else: outfname= args[1]

    print 'creating score'
    score= parser.parse(infname, cache=options.cache)
    beat_duration= float(score.tempo)/1e6
    divisions= score.divisions
    for instrument, notes in score.notes_per_instrument.iteritems():
        new_notes= [n for n in notes  \
                      if n.start/divisions*beat_duration >= moment_from and \
                         (n.start + n.duration)/divisions*beat_duration< moment_to]
        score.notes_per_instrument[instrument]= new_notes

    print 'dumping'
    writer= writerclass()
    writer.dump(score, outfname)

if __name__ == '__main__':
    main()
    




    
