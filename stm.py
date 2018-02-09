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

# stm32f1 !!!!!!

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

class enum( tuple ):
    def __new__(s, *n, **o):
        return super().__new__(s, n)
    def __init__(s, *n, **o):
        s.o = o
    def index(s, n):
        if n>len(s):
            raise ValueError('invalid index {}'.format(n))
        return n
    def dl(s):
        return zip(s, range(len(s))) # TODO: l for dropdown ?
    def m(s):
        return dict(s.l())
    def r(s, v):
        return s.index(v)

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
            ( '_fcfg_gen_setup', 'Generate setup', FS() ), # TODO: template for functions fields
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

    SPD = enum(10, 2, 5, disp=lambda n: '{} MHz'.format(n))
    IM = enum('analog', 'floating', 'up', 'down')
    OM = enum('push-pull', 'open-drain')

    @setup_params(
        ('m', 'in'), # TODO: common default set ?????????
        ('spd', SPD.rev(2)),
        ('in_mode', IM.rev('floating')),
        ('out_mode', OM.rev(0)),
        ('v', 0)
    )
    def setup_regs( s, cr, bsrr ):
        P = s.get_arg
        nn = str(s.num)
        m = P( 'm' )
        if m in ( 'out', 'afio' ):
            cr['MODE'+nn] = 1 + P( 'spd' )
            cr['CNF'+nn] = P( 'out_mode' )
            if m == 'afio': cr['CNF'+nn] |= 0x02
            bsrr[( 'BR' if P('v')==0 else 'BS' )+nn] = 1
        elif m == 'in':
            cr['MODE'+nn] = 0
            im = P( 'in_mode' )
            cr['CNF'+nn] = im
            if im >= 2:
                bsrr[( 'BR' if im==2 else 'BS' )+nn] = 1

    descr = CD(
        'GPIO pin setup',
        [
            ( 'm', 'Mode', ('out','in','afio'), {}, {'update':True} ),
#            ( 'afion', 'Afio number', (0,4), { 'm':'afio' } ),
            ( 'out_mode', 'Output mode', OM, { 'm':('afio','out') } ),
            ( 'spd', 'Output speed', SPD, { 'm':('afio','out') } ),
            ( 'in_mode', 'Input mode', IM, { 'm':('in') } ),
            ( '_fcfg_gen_setup', 'Genrate setup', FS() ),
            ( '_fcfg_val', 'Get value', FS(), { 'm':('afio','in') } ),
            ( '_fcfg_vset', 'Set high', FS(), { 'm':('afio','out') } ),
            ( '_fcfg_vreset', 'Set low', FS(), { 'm':('afio','out') } ),
            ( 'test_freq', 'Test freq', freq_setup( 'test_freq2', (1, 2, 3), (1, 2, 3) ), { 'm':('afio','out') } ),
            ( 'test_sel', 'Test selection', objsel_setup( '.', 'pin_cfg', 'gpio_pin'), { 'm':('afio','out') } ),
        ],
    )

"""
class tim_ch( config_parent ):
    @setup_params(
        ('ccm')
    )
    def setup_regs( s, ccmr, ccer ):
        P = s.get_arg
        m = P('ccm')
        ccmr['CC'+s.n+'S']=m
        if m == 0:
            p = 'OC'+s.n
            ccmr[p+'FE']=P('fast') # TODO: map parameters to registers
            ccmr[p+'PE']=P('preload')
            ccmr[p+'M']=P('om')
            ccmr[p+'CE']=P('clear')
        else:
            p = 'IC'+s.n
            ccmr[p+'PSC']=P('psc')
            ccmr[p+'F']=P('filter')

        p = 'CC'+s.n
        ccer[p+'E'] = P('en')
        ccer[p+'P'] = P('pol')
        ccer[p+'NP'] = P('compen')
        ccer[p+'NP'] = P('comppol')

        descr = CD(
            'TIM channel setup',
            [
                ( 'ccm', 'Compare / Capture mode', enum('Output', 'Capture TI1', 'Capture TI2', 'Capture TRC').l(), {}, {'update':True} ), # TODO: different map TI depending on register
                ( 'psc', 'Prescaler', enum(1, 2, 4, 8), { 'ccm':'' } ), # TODO: lambda constraint
                #( 'filter', 'Sampling frequency' ), # TODO: special widget ?
                ( 'fast', 'Prescaler', , { 'ccm':'Output' } ), # TODO: enum constraint
                ( 'preload', 'Preload', , { 'ccm':'Output' } ),
                ( 'om', enum('frozen', '1 on match', '0 on match', 'Toggle on match', 'force 0', 'force 1', '1 -> cnt<ccr', '1 -> cnt>ccr'), , { 'ccm':'Output' } ),
                ( 'clear', 'Clear on ETRF' , { 'ccm':'Output' }  ) # TODO: boolean field
            ]
        )

class tim(config_parent):
    /
"""

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


