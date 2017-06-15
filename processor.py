#!/usr/bin/python

class processor( pcfg ): # TODO: move methods to processor_descr
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
                i.get_setup()
    def __init__( s, n ):
        s.clr()
        s.ol = G__get_ol( n )
        s.descr_t = {}
        s.modes = {}
    def clr( s ):
        s.periph_data = {}
        s.types = {}
        s.vars = {}
    def wctx( s, p ): # TODO: cache ?
        pd = s.get_obj( p )
        return write_ctx( s.get_periph( pd.pname() ), s )
    def import_cfg( s, n ): # TODO: cache ?
        try:
            G__ol.get( s.n+'/'+n ) # must be global ?
        except KeyError:
            return s.parent_cfg.load_cfg( n )
    def get_periph( s, n ): # TODO: cache
        try:
            return s.periph[ n ]
        except KeyError:
            return s.parent_cfg.get_periph( n )
    def get_var( s, n ): # TODO: cache
        try:
            return s.vars[n]
        except AttributeError:
            return s.parent_cfg.get_var( n )
    # get periph regs ?


