from subprocess import PIPE, Popen
from time import sleep
def call_bin(path, stdin=None, *args, **kwargs):
    """
    params:
      path :: string
        el path del coso que queres ejecutar
      stdin :: string
        el string que se manda a stdin. Si es None no se manda nada

    todos los args que se pasan seran pasados como argumentos y 
    kwargs seran pasados como -clave valor 

    esta llamada es bloqueante
    returns:
      (stdout, sterr)
    """
    args= list(args)
    for k, v in kwargs.iteritems():
        if len(k) > 1: k= '--%s' % k
        else: k= '-%s' % k

        args.insert(0, v)
        args.insert(0, k)
    args.insert(0, path)

    if stdin is not None:
        p= Popen(args, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        res= p.communicate(stdin)
    else:
        p= Popen(args, stdout=PIPE, stderr=PIPE)
        res= p.communicate()

    return res


