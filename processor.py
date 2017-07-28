#!/usr/bin/python

from sys import modules

G__ol = xml_storable.load_obj

class processor( config_parent ):
    def write_start( s ):
        s.clks = []
        s.psets = {}
    def clk_start( s, n ):
        s.clks.append( n )
    def get_mode( s, n ):
        return mode_obj()
    def gen_code( s, wctx, f, *args, **vargs ):
        pass
    def gen_setup( s ):
        for n,i in s.__dict__.items():
            if hasattr( i, 'gen_setup' ) and not s.startswith( '_' ):
                i.gen_setup()
    def __init__( s, n ):
        s.clr()
        s.ol = G__get_ol( n )
        s.descr_t = {}
        s.modes = {}
    def wctx( s, p ): # TODO: cache
        pd = s.get_obj( p )
        return write_ctx( s.get_periph( pd.pname() ), s )
    def import_cfg( s, n ):
        try:
            r = s.load_obj(
                    '{}/{}.xml'.format( s.n, n ),
                    modules[ s.__module__ ]
                )
            r.cfg_name = n;
            return r
        except KeyError:
            return s.parent_cfg.import_cfg( n )
    def get_periph( s, n ): # TODO: cache
        try:
            return s.periph[ n ]
        except KeyError:
            return super().get_periph( n )
    def get_var( s, n ): # TODO: cache
        try:
            return s.vars[n]
        except KeyError:
            return super().get_var( n )
    # get periph regs ?

class write_ctx:
    def __init__( s, p, cfg, dmode='ww' ):
        s.dmode = dmode
        s.c = cfg;
        s.p = p
        s.o = s.c.o
    def wset( s, n, v, m=None ):
        if not m: m = s.dmode
        s.p.gen_setup( s.o, n, v, s.c.get_mode(m) )
    def clk_start( s ):
        s.c.clk_start( s.p.n )

class pcfg( config_parent ):
    def __init__( s ):
        pass
class out_proc:
    def putl( s, v ): print(v)

class mode_obj:
    zz = False
    vol = False
    zu = True
    ww = False


