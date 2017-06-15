#!/usr/bin/python

import cfg
import gui

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

class foo:
    pass

input_descr = gui.input_descr
config_descr = gui.config_descr
freq_descr = gui.freq_descr

cc = cfg.cfg( cfg.obj_loader() );
cc.descr_t = {}
cc.pn = 'nasz_procek'
cc.o = cfg.out_proc()

cc.descr_t['gpio_pin'] = config_descr(
        'GPIO pin setup',
        [
            input_descr( 'm', 'Mode', ['out','in','afio'], {}, update=True ),
            input_descr( 'afion', 'Afio number', (0,4), { 'm':'afio' } ),
            input_descr( 'out_mode', 'Output mode', [('push-pull',0),('open-drain',1)], { 'm':('afio','out') } ),
            input_descr( 'spd', 'Output speed', [ ('2MHz',2), ('10MHz',1), ('50MHz',3) ], { 'm':('afio','out') } ),
            input_descr( 'in_mode', 'Input mode', ['up','down','analog','floating'], { 'm':('in') } ),
            input_descr( 'val', 'Get value', 'func', { 'm':('afio','in') } ),
            input_descr( 'set', 'Set high', 'func', { 'm':('afio','out') } ),
            input_descr( 'reset', 'Set low', 'func', { 'm':('afio','out') } ),
#            input_descr( 'test_freq', 'Test freq', freq_descr( 'test_freq2', [1, 2, 3], [1, 2, 3] ), { 'm':('afio','out') } ),
        ],
)

cc.descr_t['gpio'] = config_descr(
        'GPIO port setup',
        [
        ],
)
#cfg.descr_t['gpio'].tiles = True

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
"""w = gui.Gtk.Window()
w.set_title( 'procek' )
w.add( gui.gen_proc_view( [ p1 ]*64 ) )
w.show_all()
w.connect("destroy",gui.Gtk.main_quit) #"""

gui.Gtk.main()
#for i in range( 1, 500000 ):
cc.write_start()
g.gen_setup( {} )
print( cc.clks )


