#!/usr/bin/python

#import cfg
import gui

ID = gui.input_descr
CD = gui.config_descr
#freq_descr = gui.freq_descr

class processor( gui.config_parent ): # TODO: processor parent class
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
#    def wctx( s, p ): # TODO: cache ?
#        pd = s.get_obj( p )
#        return write_ctx( s.get_periph( pd.pname() ), s )
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

class gpio( gui.config_parent ):
    def gen_setup( s, param ): # TODO: parametrized setup ?
        cr = {}
        bsrr = {}
        for e in s.children:
            nn = str(e.num)
            if hasattr( e, 'm' ):
                m = e.m
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

    descr = gui.config_descr(
        'GPIO port setup',
        [
        ],
    )

class gpio_pin( gui.config_parent ):
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

    descr = gui.config_descr(
        'GPIO pin setup',
        [
            ( 'm', 'Mode', ('out','in','afio'), {}, True ),
            ( 'afion', 'Afio number', (0,4), { 'm':'afio' } ),
            ( 'out_mode', 'Output mode', (('push-pull',0),('open-drain',1)), { 'm':('afio','out') } ),
            ( 'spd', 'Output speed', ( ('2MHz',2), ('10MHz',1), ('50MHz',3) ), { 'm':('afio','out') } ),
            ( 'in_mode', 'Input mode', ('up','down','analog','floating'), { 'm':('in') } ),
            ( 'val', 'Get value', gui.func_setup(), { 'm':('afio','in') } ),
            ( 'vset', 'Set high', gui.func_setup(), { 'm':('afio','out') } ),
            ( 'vreset', 'Set low', gui.func_setup(), { 'm':('afio','out') } ),
            ( 'test_freq', 'Test freq', gui.freq_setup( 'test_freq2', (1, 2, 3), (1, 2, 3) ), { 'm':('afio','out') } ),
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

