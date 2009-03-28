from impl import StrFreqDict

d= StrFreqDict()
strs= 'hola', 'hol', 'holae', 'hola', 'hole'

for str in strs:
    d.add(str)

print '\n'.join(d.get_grammar())
#assert d.get_freq('hola') == 2
#assert d.get_freq('hol') == 1
#assert d.get_freq('hl') == 0
#assert d.get_freq('holae') == 1

#assert d.n_continuations('h') == 4
#assert d.n_continuations('hol') == 3
#assert d.n_continuations('hola') == 1
#assert d.n_continuations('holae') == 0

