#!/usr/bin/python

from sys import modules

from gui import *
from copy import copy
from periph_class import proc_cfg

class processor( config_parent ):
    proc_cfg = None
    def write_start( s ):
        s.clks = []
        s.psets = {}
        s._wctx = write_ctx(s.proc_cfg, )
    def get_mode( s, n ):
        return mode_obj()
    def __init__( s ):
        s.clr()
        s.descr_t = {}
        s.modes = {}
        s._imp_ch = {}
    def wctx( s ):
        return write_ctx( s.get_periph )
    def import_cfg( s, n ):
        try:
            return s._imp_ch[n]
        except KeyError:
            r = s.proc_cfg.import_cfg( n )
            s._imp_ch[n] = r
            return r
    def get_reg_doc( s, tn, fn=None, bn=None ):
        t = s.proc_cfg.get_type( tn )
        if not fn: return t.doc
        f = t._t[fn]
        if not bn: return f.doc
        b = f.b[bn]
        return b.doc
    #def gen_code( s ):
    #    # TODO: include ? startup ?
    #    super().gen_code()

class write_ctx:
    def gen_setup( s, p, fn, fl, mode ): # TODO: faster version in C++
        ln = s.ln
        f = p.t._t[ fn ]
        ln('   /* {}: {}  */', f.get_descr(),fl)
        zu = mode.zu
        zz = mode.zz
        if zz: zu=False
        ne = getattr( f, 'ne', 1 )
        vv = [0]*ne
        nbits = f.l*8
        ones = (1<<nbits)-1
        if zu:
            uu = [ones]*ne
        for n,v in fl.items():
            ff = f.b[ n ]
            nn = ff.b//nbits
            ss = ff.b %nbits
            vv[nn] |= int(v)<<ss # TODO: unconstant value, cut bits option
            if zu and not mode.ww:
                uu[nn] &= ~(((1<<(1 if not hasattr(ff,'e') else ((ff.e%nbits)-ss+1)))-1)<<ss);
        fpos = p.a+f.off;
        pp =( '=' if zz or mode.ww else '|=' ) # preserve previous
        vol = ( 'volatile ' if mode.vol else '' )
        for it in range(len(vv)): # TODO: preserve current vals
            fp = '( *({}uint{}_t*){})'.format(vol, f.l*8, hex(fpos+it*f.l))
            nv = None
            av = None
            if zz or vv[it]!=0:
                nv = '0x%0*x' % (nbits//4,vv[it])
            if zu and uu[it]!=ones:
                av = '0x%0*x' % (nbits//4,uu[it])
            if av and nv:
                ln('{0}=((({0})&({1}))|({2}));', fp, av, nv)
            elif nv:
                ln(fp+pp+nv+';')
            elif av:
                ln('({})&=({});', p, av) # TODO: negate flag
    def __init__( s, g, m=None ):
        s.m = m if m else write_mode()
        s.g = g
    def cperiph( s, n, **v ):
        p = s.g( n )
        for n,v in v.items():
            s.gen_setup( p, n, v, s.m )
#    def wset( s, n, v, m=None ):
#        if not m: m = s.dmode
#        s.gen_setup( s.o, n, v, s.c.get_mode(m) )
    def ln( s, t, *a, **aa ):
        print( t.format(*a, **aa) )

class pcfg( config_parent ):
    def __init__( s ):
        pass

class write_mode:
    zz = False # zero all
    vol = False # volatile
    zu = True # zero used
    ww = False # write only - unset fields to zeros

    def set(s, **o):
        r = copy(s)
        r.__dict__.update(o)
        return r



