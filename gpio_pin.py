class gpio_pin( gui.config_parent ):
    def setup( s, c ):
        s.num = int( c.num )
        s.p = [ c.p ]
        s.n = c.n
        #G__cfg.mark_locked(s.p.n+'_'+s.num)
        #G__cfg.mark_used(s.p.n)
    def gen_set( s ):
        pass

    def descr_color( s ):
        return 'green'
    def descr_line( s ):
        return 'name: '+s.n
    def descr_short( s ):
        return 'name: '+s.n
    def descr_pname( s ):
        return s.p[0].descr_pname()+str(s.num)


