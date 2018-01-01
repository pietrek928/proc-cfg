#!/usr/bin/python

from gui import *
from processor import *
from periph_class import load_proc_cfg

# end plan:
# - create processor
# - add objects
# - init clocks
# - rest of the setup
# - gen other functions

CD = config_descr
FS = func_setup
#freq_descr = gui.freq_descr

parent_cfg = processor.proc_cfg
class processor( processor ):
    model = __name__ # TODO: single function
    proc_cfg = load_proc_cfg( cm=modules[__name__], cfg_dir='periph_config/'+model, f='periph_config/{}.xml'.format(model), pcfg=parent_cfg )
    get_periph = proc_cfg.get_periph
    def write_start( s ):
        s.clks = []
        s.psets = {}
    def get_mode( s, n ):
        return mode_obj()
    def gen_code( s, wctx, f, *args, **vargs ):
        pass
    def __init__( s ):
        s.clr()
        s.descr_t = {}
        s.modes = {}
    def clr( s ):
        s.periph_data = {}
        s.types = {}
        s.vars = {}
    def cstart( s, n ):
        s.wctx().gen_setup(s.get_periph('RCC'), 'ENR', {n+'EN':1}, write_mode())
#    def wctx( s, p ): # TODO: cache ?
#        pd = s.get_obj( p )
#        return write_ctx( s.get_periph( pd.pname() ), s )
    # get periph regs ?

class gpio( config_parent ):
    @gen_func()
    def gen_setup( s ): # TODO: parametrized setup ?
        cr = {}
        bsrr = {}
        for e in s.child_order:
            e = getattr( s, e )
            e.setup_regs( cr, bsrr )
        print(cr, bsrr)
        s.clk_start()
        s.wctx().cperiph(s.pname(),
                    CR=cr,
                    BSRR=bsrr )

    def pname( s ):
        return 'GPIO'+s.id
    def clk_name( s ):
        return 'IOP'+s.id
    def descr_pname( s ):
        return 'P'+s.id

    descr = CD(
        'GPIO port setup',
        [
            ( '_fcfg_gen_setup', 'Generate setup', FS() ),
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

    @setup_params(
        ('m', 'in'),
        ('spd', 2),
        ('in_mode', 'floating'),
        ('out_mode', 0), # TODO: enum class ?
        ('v', 0)
    )
    def setup_regs( s, cr, bsrr ):
        P = s.get_arg
        nn = str(s.num)
        m = P( 'm' )
        if m in ( 'out', 'afio' ):
            cr['MODE'+nn] = P( 'spd' )
            cr['CNF'+nn] = 2 + P( 'out_mode' )
            bsrr[( 'BR' if P('v')==0 else 'BS' )+nn] = 1
            if m == 'afio': cr['CNF'+nn] |= 0x02
        elif m == 'in':
            cr['MODE'+nn] = 0
            im = P( 'in_mode' )
            if im == 'analog': cr['CNF'+nn] = 0
            elif im == 'floating': cr['CNF'+nn] = 1
            else:
                cr['CNF'+nn] = 2
                bsrr[( 'BR' if im=='down' else 'BS' )+nn] = 1

    descr = CD(
        'GPIO pin setup',
        [
            ( 'm', 'Mode', ('out','in','afio'), {}, {'update':True} ),
            ( 'afion', 'Afio number', (0,4), { 'm':'afio' } ),
            ( 'out_mode', 'Output mode', (('push-pull',0),('open-drain',1)), { 'm':('afio','out') } ),
            ( 'spd', 'Output speed', ( ('2MHz',2), ('10MHz',1), ('50MHz',3) ), { 'm':('afio','out') } ),
            ( 'in_mode', 'Input mode', ('up','down','analog','floating'), { 'm':('in') } ),
            ( '_fcfg_gen_setup', 'Genrate setup', FS() ),
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


