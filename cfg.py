#!/usr/bin/python

import periph_class

# TODO: xml_load
class obj_loader:
    def __init__( s, l, n ):
        s.clr()
        s.l = l
        s.d = n+'/'
    def clr( s ):
        s.obj_tab = {}
    def get( s, n ):
        try:
            return s.obj_tab[n]
        except KeyError:
            try:
                r = s.l(  s.d+n+'.xml' )
                s.obj_tab[n] = r
                return r
            except AttributeError as e:
                return None
            except Exception:
                s.obj_tab[n] = None
                return None

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
    def xml_load( s, f )
        e = Et.parse(f).getroot()
        r = xml_storable.xml_load( s, e )
        r.p = r
        return r
    def xml_store( s, f ):
        pp = Et.Element('cfg')
        xml_storable.xml_store( s, pp )
        Et.ElementTree( pp ).write( xml_file )

class out_proc:
    def putl( s, v ): print(v)

class mode_obj:
    zz = False
    vol = False
    zu = True
    ww = False


