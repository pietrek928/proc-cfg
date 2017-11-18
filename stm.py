#!/usr/bin/python

from gui import *
from processor import *
from periph_class import load_proc_cfg

ID = input_descr
CD = config_descr
FS = func_setup
#freq_descr = gui.freq_descr

# TODO: single function
processor_name = __name__
processor_cfg = load_proc_cfg( cm=modules[__name__], cfg_dir='periph_config/'+__name__, f='periph_config/{}.xml'.format(processor_name), pcfg=processor_cfg )

class processor( processor ): # TODO: processor parent class
    _proc_cfg = processor_cfg
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
            if hasattr( i, 'gen_setup' ) and not i.startswith( '_' ):
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
#    def wctx( s, p ): # TODO: cache ?
#        pd = s.get_obj( p )
#        return write_ctx( s.get_periph( pd.pname() ), s )
    # get periph regs ?

class param_t:
    def __init__( s, dv=None, p=False ):
        if p:
            s.p = p
        if dv is not None:
            d.dv = dv
    def __call__( s, o ):
        v = getattr( s, 'dv', None )
        try:
            return ( # TODO: type, link ?
                    getattr( o, v, None ) if v.startswith('$') else v
                )
        except AttributeError:
            return v
    def isp( s ):
        return getattr( s, 'p', None )
P = param_t

# TODO: wctx, force inline
def gen_func( f, *params ): # TODO: name prefix ? object, class, namespace ?
    def r( s, **args ): # c / c++ selection ?
        try:
            c = getattr( s, '_fcfg_'+f.__name__ )
        except AttributeError:
            c = None; # blank func config
            setattr( s, '_fcfg_'+f.__name__, c ) # TODO: fixing parameter function
        # TODO: unenabled function warning
        fn = '{}_{}'.format( s.n, f.__name__ ) # TODO: put func in class ?
        if args.get('decl',None):
            ln('{} {}({}){{'.format( # TODO: attrs ?
                'void', # TODO: configure return type
                fn,
                ','.join([
                    '{} {}'.format(str(v.t),n) for n,v in params
                ])
            ))
            f(s,**{ n:(args[n] if n in args else v(s)) for n,v in params})
            ln('}')
        else:
            args.update({n:v(s) for n,v in params if n not in args}) # TODO: force inline on const change
            if args.get('inline',None):
                return f( s, **args ) # TODO: conversion ? return type ?
            v = ','.join([ args['n'] for n,v in params if v.isp() ]) # TODO: multiple func versions
            if args.get('vr',None):
                vr = args['vr']
                ln('{} {} = {}({});'.format(vr.t,vr.n,s.n,v))
                return vr
            else:
                ln('{}({});'.format(fn,v))
    return r

class gpio( config_parent ):
    @gen_func(
            ('mode', P('in')),
            ('out_mode', P(0)),
            ('in_mode', P('floating')),
            ('out_mode', P(0)), # TODO: enum class ?
    )
    def gen_setup( s, **P ): # TODO: parametrized setup ?
        cr = {}
        bsrr = {}
        for e in s.children:
            nn = str(e.num)
            m = e.get_val( 'm', P('mode') ) # TODO: unify
            if m in ( 'out', 'afio' ):
                cr['MODE'+nn] = e.get_val( 'spd', 2 )
                cr['CNF'+nn] =  ( 0 if m=='in' else 2 )+e.get_val( 'out_mode', 0 )
                if hasattr( e, 'v' ): bsrr[( 'BR' if e.v==0 else 'BS' )+nn] = 1
                if m == 'afio': cr['CNF'+nn] |= 0x02
            elif m == 'in':
                cr['MODE'+nn] = 0
                im = e.get_val( 'in_mode', 'floating' )
                if im == 'analog': cr['CNF'+n] = 0
                elif im == 'floating': cr['CNF'+n] = 1
                else:
                    cr['CNF'+nn] = 2
                    bsrr[( 'BR' if im=='down' else 'BS' )+nn] = 1
        ctx = s.wctx()
        ctx.clk_start()
        ctx.wset( 'CRL' , cr )
        ctx.wset( 'BSRR', bsrr )

    def pname( s ):
        return 'GPIO'+s.id
    def descr_pname( s ):
        return 'P'+s.id

    descr = CD(
        'GPIO port setup',
        [
        ],
    )

class gpio_pin( config_parent ):
#    def setup( s, c ):
#        s.num = int( c.num )
#        s.n = c.n
#        #G__cfg.mark_locked(s.p.n+'_'+s.num)
#        #G__cfg.mark_used(s.p.n)
    def gen_set( s ):
        pass

    def descr_color( s ):
        return 'green'
    def descr_line( s ):
        return 'name: '+s.n
    def descr_short( s ):
        return 'name: '+s.n
    def descr_pname( s ):
        return s._p.descr_pname()+str(s.num)

    descr = CD(
        'GPIO pin setup',
        [
            ( 'm', 'Mode', ('out','in','afio'), {}, True ),
            ( 'afion', 'Afio number', (0,4), { 'm':'afio' } ),
            ( 'out_mode', 'Output mode', (('push-pull',0),('open-drain',1)), { 'm':('afio','out') } ),
            ( 'spd', 'Output speed', ( ('2MHz',2), ('10MHz',1), ('50MHz',3) ), { 'm':('afio','out') } ),
            ( 'in_mode', 'Input mode', ('up','down','analog','floating'), { 'm':('in') } ),
            ( '_fcfg_val', 'Get value', FS(), { 'm':('afio','in') } ),
            ( '_fcfg_vset', 'Set high', FS(), { 'm':('afio','out') } ),
            ( '_fcfg_vreset', 'Set low', FS(), { 'm':('afio','out') } ),
            ( 'test_freq', 'Test freq', freq_setup( 'test_freq2', (1, 2, 3), (1, 2, 3) ), { 'm':('afio','out') } ),
            ( 'test_sel', 'Test selection', objsel_setup( '.', 'pin_cfg', 'gpio_pin'), { 'm':('afio','out') } ),
        ],
    )

"""
p1 = gpio_pin()
p2 = gpio_pin()
g = gpio()
p1.n = 'test_pin1'
p2.n = 'test_pin2'
p1.p = [g]
p1.num = 5
p2.p = [g]
p2.num = 6
p1.test_freq2 = '8e6'
p2.test_freq2 = '7e6'
g.n = 'gpio_test'
g.id = 'A'
g.cfg = cc
g.add_child( p1 )
g.add_child( p2 )
g.show_window().connect("destroy",gui.Gtk.main_quit)
#w = gui.Gtk.Window()
#w.set_title( 'procek' )
#w.add( gui.gen_proc_view( [ p1 ]*64 ) )
#w.show_all()
#w.connect("destroy",gui.Gtk.main_quit)

gui.Gtk.main()
#for i in range( 1, 500000 ):
cc.write_start()
g.gen_setup( {} )
print( cc.clks )#"""


