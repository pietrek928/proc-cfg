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

    def __init__( s ):
        super().__init__()
        s.clr()
        s.descr_t = {}
        s.modes = {}
    def write_start( s ):
        s.clks = [] # TODO: as cache ?
        s.psets = {}
    def get_mode( s, n ):
        return mode_obj()
    def gen_code( s, wctx, f, *args, **vargs ):
        pass
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
        'GPIO port setup', [
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

    @setup_params(
        ('m', 'in'), # TODO: common default set ?????????
        ('spd', 2),
        ('in_mode', 'floating'),
        ('out_mode', 'push-pull'),
        ('v', 0)
    )
    def setup_regs( s, cr, bsrr ):
        P = s.get_arg_f() # TODO: put in decorator
        nn = str(s.num)
        m = P( 'm' )
        if m in ( 'out', 'afio' ):
            cr['MODE'+nn] = 1 + P( 'spd' )
            cr['CNF'+nn] = P( 'out_mode' )
            if m == 'afio': cr['CNF'+nn] |= 0x02
            bsrr[( 'BR' if P('v') else 'BS' )+nn] = 1
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
            ( 'out_mode', 'Output mode', 'ENUM', { 'm':('afio','out') } ),
            ( 'spd', 'Output speed', 'ENUM', { 'm':('afio','out') } ),
            ( 'in_mode', 'Input mode', 'ENUM', { 'm':('in') } ),
            ( '_fcfg_gen_setup', 'Genrate setup', FS() ),
            ( '_fcfg_val', 'Get value', FS(), { 'm':('afio','in') } ),
            ( '_fcfg_vset', 'Set high', FS(), { 'm':('afio','out') } ),
            ( '_fcfg_vreset', 'Set low', FS(), { 'm':('afio','out') } ),
            ( 'test_freq', 'Test freq', freq_setup( 'test_freq2', (1, 2, 3), (1, 2, 3) ), { 'm':('afio','out') } ),
            ( 'test_sel', 'Test selection', objsel_setup( '.', 'pin_cfg', 'gpio_pin'), { 'm':('afio','out') } ),
        ],
        enums=enum_map(
            spd= enum(10, 2, 5, disp=lambda n: '{} MHz'.format(n)),
            in_mode= enum('analog', 'floating', 'up', 'down'),
            out_mode= enum('push-pull', 'open-drain')
        )
    )

class tim_ch( config_parent ):
    # TODO: different map TI depending on register, separate class ?

    @setup_params()
    def setup_regs( s, ccmr, ccer ):
        P = s.get_arg_f()
        ccmr['CC'+s.n+'S']=P('ccm')
        m = s.ccm
        if m == 'Output':
            set_multi( ccmr, 'OC'+s.n,
                FE=P('fast'),  # TODO: map parameters to registers
                PE=P('preload'),
                M=P('out_mode'),
                CE=P('clear')
            )
        else:
            set_multi( ccmr, 'IC'+s.n,
                PSC=P('psc'),
                F=P('filter')
            )

        set_multi( ccer, 'CC'+s.n,
            E = P('en'),
            P = P('pol'),
            NE = P('compen'),
            NP = P('comppol')
        )

        descr = CD(
            'TIM channel setup',
            [
                ( 'ccm', 'Compare / Capture mode', CCM, {}, {'update':True} ),
                ( 'psc', 'Prescaler', 'ENUM', { 'ccm': 'Capture*' } ), # TODO: expr?
                #( 'filter', 'Sampling frequency' ),
                # TODO: filter frequency widget ?
                ( 'fast', 'Fast', BF(), { 'ccm':'Output' } ),
                ( 'preload', 'Preload', BF(), { 'ccm':'Output' } ),
                ( 'out_mode', 'Output mode', 'ENUM', {}, { 'ccm':'Output' } ),
                ( 'clear', 'Clear on ETRF', BF(), { 'ccm':'Output' }  )
            ]
        )
        enums=enum_map(
            ccm= enum('Output', 'Capture TI1', 'Capture TI2', 'Capture TRC'),
            psc= enum(1, 2, 4, 8),
            out_mode= enum('frozen', '1 on match', '0 on match', 'Toggle on match',
                'force 0', 'force 1', '1 <- cnt<ccr', '1 <- cnt>ccr')
        )

class tim(config_parent):

    @gen_func()
    @setup_params()
    def gen_setup( s ):
        P = s.get_arg_f()
        ccmr = {}
        ccer = {}
        for e in s.child_order:
            e = getattr( s, e )
            e.setup_regs( ccmr, ccer )
        print(ccmr, ccer)
        s.clk_start()
        """cr = {
            'CEN': ,
            'UDIS': ,
            'URS': ,
            'OPM': ,
            'DIR': ,
            'CMS': ,
            'ARPE': ,
            'CKD': ,
            'CCPC': ,
            'CCUS': ,
            'CCDS': ,
            'MMS': ,
            'TI1S': ,
            '': ,
        } # """
        s.wctx().cperiph(s.pname(),
                    CCMR=ccmr,
                    CCER=bsrr )

    def pname( s ):
        return 'TIM'+s.id
    def clk_name( s ):
        return 'TIM'+s.id

    descr = CD(
        'Timer setup', [
            ( '_fcfg_gen_setup', 'Generate setup', FS() ),
        ]
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


