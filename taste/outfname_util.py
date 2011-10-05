import os
from datetime import datetime

def get_outfname(out_basepath, infname= None, override=False, outfname=None, path_suffix=None):        
    if outfname is None and infname is None: raise Exception()

    outpath= os.path.abspath(os.path.join(out_basepath, datetime.now().strftime('%Y-%m-%d')))
    if path_suffix is not None: outpath= os.path.join(outpath, path_suffix)

    if not os.path.isdir(outpath):
        print "Creating dir", outpath
        os.makedirs(outpath)

    if outfname is None: outfname= os.path.basename(infname).lower()
    # -4 por el .mid +1 por el -
    basename, ext= os.path.splitext(outfname)
    versions= [fname[len(basename)+1:-len(ext)] for fname in os.listdir(outpath) if fname.startswith(basename) and fname.endswith(ext)]
    versions= [s for s in versions if len(s) > 0]
    for i in reversed(xrange(len(versions))):
        if not versions[i].isdigit():
            versions.pop(i)
        else:
            versions[i]= int(versions[i])
    if len(versions) == 0:
        versions= [0]
    outfname= '%s-%s%s' % (basename, max(versions)+1, ext)
    
    outfname= os.path.join(outpath, outfname)
    return outfname



def get_outfname2(out_basepath, infname, out_extension=None, fname_suffix=None, override=False, path_suffix=None): 
    outpath= os.path.abspath(os.path.join(out_basepath, datetime.now().strftime('%Y-%m-%d')))
    if path_suffix is not None: outpath= os.path.join(outpath, path_suffix)

    if not os.path.isdir(outpath):
        print "Creating dir", outpath
        os.makedirs(outpath)
    if os.path.exists('output'): os.unlink('output')
    os.system('ln -s %s output' % outpath)

    outfname= os.path.basename(infname).lower()
    if out_extension is not None:
        name, ext= os.path.splitext(outfname)
        outfname= '%s.%s' % (name, out_extension)

    fname_suffix= fname_suffix or ''

    name, ext= os.path.splitext(outfname)
    if override: return os.path.join(outpath, '%s%s%s' % (name, fname_suffix, ext))
    suffixed_outfname= '%s-00%s%s' % (name, fname_suffix, ext)

    if suffixed_outfname in os.listdir(outpath):
        basename, ext= os.path.splitext(outfname)
        versions= [fname[len(basename)+1:-len(ext)-len(fname_suffix)] for fname in os.listdir(outpath) if fname.startswith(basename) and fname.endswith(ext) and fname_suffix in fname]
        versions= [s for s in versions if len(s) > 0]

        for i in reversed(xrange(len(versions))):
            if not versions[i].isdigit():
                versions.pop(i)
            else:
                versions[i]= int(versions[i])
        if len(versions) == 0:
            versions= [0]
        outfname= '%s-%02d%s%s' % (basename, max(versions)+1, fname_suffix, ext)
    else:
        outfname= suffixed_outfname
    
    outfname= os.path.join(outpath, outfname)
    return outfname




