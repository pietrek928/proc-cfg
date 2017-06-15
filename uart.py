#!/usr/bin/python

import cfg
import gui

class uart( gui.config_parent ):
    def setup( s, c ):
        s.id = c.id
        s.n = 'UART'+s.id
        #G__cfg.mark_lock('GPIO'+s.id)
    def gen_setup( s, param ):
        ctx = s.wctx()
        ctx.clk_start()
        #ctx.wset( 'CRL',  cr )
        #ctx.wset( 'BSRR',  bsrr )
#    def xml_store( s, e ):
#        /
#    def descr_title( s ):
#        /
    def descr_short( s ):
        r = ''
        for e in s.children:
            r += e.descr_line()
            r += '\n'
    def pname( s ):
        return 'USART'+s.id
    def descr_pname( s ):
        return 'UART'+s.id

cc.descr_t['uart'] = config_descr(
        'UART setup',
        [
            input_descr( 'tx_pin', 'TX pin', pin_descr( 'tx' ), {} )
            input_descr( 'rx_pin', 'RX pin', pin_descr( 'rx' ), {} )
#            input_descr( 'test_freq', 'Test freq', freq_descr( 'test_freq2', [1, 2, 3], [1, 2, 3] ), { 'm':('afio','out') } ),
        ],
)


