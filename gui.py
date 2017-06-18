#!/usr/bin/python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository.Gdk import color_parse
import xml.etree.ElementTree as Et

ld_base = {
    's': str,
    'i': int,
    'f': float,
    'b': bool
}
ld_base_r = dict( tuple(reversed(i))
                for i in ld_base.items() )

def store_obj( e, o ):
    t = type(o)
    if t in ld_base_r:
        e.attrib[ 't' ] = ld_base_r[t]
        e.attrib[ 'v' ] = str( o )
    else:
        try:
            o.xml_store( e )
        except KeyError:
            pass


def flush_children( o ):
    for i in o.get_children():
        o.remove( i )

class xml_storable:
    def load_obj( s, e, cm ):
        t = e.get('t')
        if t in ld_base:
            return ld_base[t]( ee.attrib['v'] )
        else:
            r = cm.get(t)().xml_load( e, cl )
            r._p = s
            return r

    def xml_store( s, e ):
        e.attrib[ 't' ] = type(s).__name__;
        for n,v in s.__dict__.items():
            if not n.startswith('_'):
                ee = Et.SubElement( e, n )
                store_obj( ee, v )
    def xml_load( s, e, cm ):
        for n,i in e.attrib.items():
            setattr( s, n, str(i) )
        for ee in e:
            setattr( s, ee.tag, s.load_obj( ee, cm ) )
        return s

def activate_func_cb( e, o ):
    if not e.get_expanded():
        if not o.editing():
            e.add( o.show() )
            e.show_all()
    else:
        for i in e.get_children():
            if isinstance( i, Gtk.Box ):
                e.remove( i )

def query_tooltip_func_cb( iv, x, y, kbd, tp, o ):
    pp = iv.get_path_at_pos( x, y )
    if pp is None: return False
    m = iv.get_model()
    e = m.get_value( m.get_iter( pp ), 2 )
    tp.set_text( e.get_tooltip() )
    iv.set_tooltip_cell( tp, pp )
    return True
    #iv = o.iv
    #for (i,pp) in o.tooltip_tab:
        #iv.set_tooltip_cell( i, pp )

def cnv_num( n ):
    n = float( n )
    k = ''
    if   n >= 1e9: k='G'; n/=1e9
    elif n >= 1e6: k='M'; n/=1e6
    elif n >= 1e3: k='k'; n/=1e3
    if   n >= 1e2: nn='{:.2f}'.format(n)
    elif n >= 1e1: nn='{:.3f}'.format(n)
    else: nn='{:.4f}'.format(n)
    return nn+k

class link_path:
    def get( s, l ):
        for i in l.split( '/' ):
            if i.startswith( '.' ):
                if i == '..':
                    s = s._p
                elif i == '...':
                    s = s.cfg
                #elif i == '.$':
                else:
                    raise ValueError( 'invalid path command: \'%s\'' % str(i) )
            else:
                s = getattr( s, i )
        return s

    def unlink( s, l ):
        t = l.split('/')
        o = s.get( t[:-1] )
        n = t[-1]
        try:
            getattr( o, n ).remove()
        except AttributeError:
            pass
        delattr( o, n )

    def set( s, l, v ):
        t = l.split('/')
        o = s.get( t[:-1] )
        n = t[-1]
        try:
            getattr( o, n ).remove()
        except AttributeError:
            pass
        setattr( o, n, v )

    def get_obj_list( s, t ):
        o = s._p
        o = s.get()
        r = []
        for n,i in o.__dict__.items():
            if isinstance( i, t ):
                r.append( ( n, t.n ) )
        return r

class config_descr:
    def __init__( s, d, tt, ff=[] ):
        s.d = d
        s.tt = [ input_descr( *i ) for i in tt ]
        s.ff = ff

class input_descr( xml_storable ):
    def __init__( s, n, vd, fv, sl, update=False, pdescr=None ):
        s.n = n
        s.vd = vd
        s.fv = fv
        s.sl = sl
        if update: s.update = update
        if pdescr: s.pdescr = pdescr

    def up( s ):
        return ( hasattr(s,'update') and s.update )

def change_list_cb( cb, s, n, ucb=None ):
    model = cb.get_model()
    index = cb.get_active()
    setattr( s, n, model[index][-1] )
    if ucb: ucb()

# o: object that contains variable
# n: variable name
# f: option list, tuple: ( descr, value )
# ucb: update callback on change
def gen_combo( o, n, f, ucb=None ):
    ee = f[0]
    ii = 0
    _ii = 0
    vv=getattr( o, n, None )
    if isinstance( ee, tuple ):
        names = Gtk.ListStore( type(ee[0]), type(ee[1]) )
        for a in f:
            names.append( list( a ) )
            if a[-1] == vv: ii=_ii
            _ii+=1
        ee = ee[1]
    else:
        names = Gtk.ListStore( type(ee) )
        for a in f:
            names.append( [ a ] )
            if a == vv: ii=_ii
            _ii+=1
    if not hasattr( o, n ): setattr( o, n, ee )
    cb = Gtk.ComboBox.new_with_model(names)
    cb.set_active( ii )
    r = Gtk.CellRendererText()
    cb.pack_start(r, True)
    cb.add_attribute( r, 'text', 0 )
    cb.connect("changed", change_list_cb, o, n, ucb)
    return cb

def gen_proc_view( t ):
    tl = len( t )//4
    tt = Gtk.Table(tl+2, tl+2, False) # TODO: move to grid
    it=0
    for i in t:
        ld = Gtk.Label( i.descr_line() )
        ld.modify_bg( Gtk.StateFlags.NORMAL, color_parse(i.descr_color()) )
        nn = it//tl
        nr = it%tl
        ori = ( Gtk.Orientation.VERTICAL if (nn%2==1) else Gtk.Orientation.HORIZONTAL )
        pprev = ( nn==1 or nn==2 )
        ang = 90*(nn%2)
        ld.set_angle( ang )
        if   nn==0: cc=1; rr=nr+2;
        elif nn==1: cc=nr+2; rr=tl+2;
        elif nn==2: cc=tl+2; rr=tl-nr+1;
        elif nn==3: cc=tl-nr+1; rr=1;
        b = Gtk.Box(orientation=ori)
        lp = '('+str(it+1)+')'
        lpp = i.descr_pname()
        lp = Gtk.Label( lpp+lp if nn<=1 else lp+lpp );
        lp.set_angle( ang )
        if pprev: b.add(lp)
        b.add(ld)
        if not pprev: b.add(lp)
        tt.attach( b, cc-1, cc, rr-1, rr )
        it+=1
    return tt

class config_parent( link_path, xml_storable ):
    def get_icon( s ):
        if hasattr( s, 'icon' ): return s.icon
        cd = s.get_descr_class()
        if hasattr( cd, 'icon' ): return cd.icon
        return 'edit-copy'

    def get_val( s, n, default ):
        if hasattr( s, n ): return getattr( s, n )
        return default

    def has_val( s, n, v ):
        return hasattr( s, n ) and getattr( s, n )==v

    def get_cfg( s, n ):
        try:
            while not hasattr( s, n ): s=s._p
        except (AttributeError,KeyError):
            return None
        return getattr( s, n )

    def wctx( s ):
        return s.get_cfg( '_wctx' )

    def start_clk( s ):
        s.get_cfg('start_clk')( s.n )

    def get_tooltip( s ):
        if not hasattr( s, 'descr_short' ): return s.n
        return s.descr_short()

    def update_all( s ):
        if hasattr( s, 'update' ): s.update()
        if s.editing():
            flush_children( s._pb )
            pb = s._pb
            s.show( pb )

    def editing( s ):
        return hasattr( s, '_pb' )

    def close( s ):
        delattr( s, '_pb' )

    def rollup( s ):
        if hasattr( s, '_pb' ):
            del s._pb

    def show_window( s ):
        w = Gtk.Window()
        w.set_title( s.get_val( 'name', s.n ) )
        w.add( s.show() )
        w.show_all()
        return w

    def del_child( s, n ):
        try:
            getattr( s, n ).remove()
            delattr( s, n )
        except ( KeyError, AttributeError ):
            pass

    def remove( s ): #TODO: list ?
        for n,i in s.__dict__.items():
            if hasattr( i, 'remove' ) and not n.startswith( '_' ):
                i.remove()

    def configure_child( s, n, n_cfg ):
        try:
            e = getattr( s, n )
            # TODO; check lock
            e.load_cfg( n_cfg )
            #e.reconfigure( n_cfg )
        except KeyError:
            pass # TODO: log

    def load_cfg( s, cfg_name ):
# TODO: flush vars
# TODO: configure children ? hide ?
        s.cfg_name = cfg_name # TODO: check differences, update
        return s.get_cfg( 'import_cfg' )( cfg_name );

    def parent_set_cb( s, c, p ):
        if not c.get_parent():
            s.close()

    def hasopt( s, n ):
        return hasattr( s, n ) and getattr( s, n )

    def descr_short( s ):
        r = ''
        for i in s.__dict__.items():
            if hasattr( i, 'descr_line' ):
                r += e.descr_line()
                r += '\n'
        return r

    def show( s, pb=None ):
        s.rollup()
        if not pb:
            pb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            pb.connect( 'parent-set', s.parent_set_cb )
        s._pb = pb
        cd = s.descr
        ucb = s.update_all
        for i in cd.tt:
            n = i.n
            u = not i.sl
            for a,v in i.sl.items():
                if hasattr(s,a):
                    a = getattr(s,a)
                    if isinstance( v, tuple ):
                        if a in v: u = True
                    elif a == v: u = True
            if u:
                b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                pb.add( b )
                b.add( Gtk.Label( i.vd ) )
                f = i.fv
                if isinstance( f, tuple ):
                    b.add( gen_combo( s, n, f, ucb=( s.update_all if i.up() else None ) ) )
                elif isinstance( f, str ):
                    pass
                else:
                    d = getattr( s, n, None )
                    if not d:
                        d = f.obj()
                        d._p = s
                        setattr( s, n, d )
                    l = f.disp( d, ucb )
                    for c in l: b.add( c )
            elif hasattr( s, n ): delattr( s, n )
        if hasattr( cd, 'tiles' ) and cd.tiles:
            il = Gtk.ListStore( Pixbuf, str, object )
            iv = Gtk.IconView()
            iv.set_model( il )
            iv.set_pixbuf_column( 0 )
            iv.set_text_column( 1 )
            for n,i in s.__dict__.items():
                if isinstance( i, config_parent ):
                    pixbuf = Gtk.IconTheme.get_default().load_icon(i.get_icon(), 64, 0)
                    pp = il.get_path( il.append([pixbuf, i.n, i ]) )
            iv.set_property( 'has-tooltip', True )
            iv.connect( 'query-tooltip', query_tooltip_func_cb, s ) # TODO: method from class
            pb.add( iv )
        else:
            for n,i in s.__dict__.items():
                if isinstance( i, config_parent ):
                    e = Gtk.Expander( label=i.get_val( 'name', i.n ) )
                    e.connect( 'activate', activate_func_cb, i ) # TODO: method from class
                    pb.add( e )
        pb.show_all()
        return pb

    def tree_node( s, t, p ):
        tn = t.append( p, [ i.n, s ] ) # TODO: icon
        s._tn = tn

class freq( xml_storable ):
    def __init__( s ):
        s.mul = 1
        s.div = 1
    def update( s ):
        src_freq = s._p.get(s.l)
        s.freq = float(src_freq)*float(s.mul)/float(s.div)

class freq_setup:
    def __init__( s, l, mul, div=() ):
        s.__dict__.update(locals())
        del s.s
    def obj( s ):
        r = freq()
        r.l = s.l
        return r
    def disp( s, fo, cb ):
        r = [ Gtk.Label( 'X' ) ]
        if isinstance( s.mul, tuple ):
            r.append( gen_combo( fo, 'mul', s.mul, cb ) )
        r.append( Gtk.Label( '/' ) )
        if isinstance( s.div, tuple ):
            r.append( gen_combo( fo, 'div', s.div, cb ) )
        fo.update()
        r.append( Gtk.Label( '= '+cnv_num( fo.freq )+'Hz' ) )
        return r

class func( xml_storable ):
    def __init__( s ):
        s.en = False
    def update_cb( s, cb, nc, ucb=None ):
        v = cb.get_active()
        setattr( s, nc, v )
        if ucb: ucb()

class func_setup:
    def obj( s ):
        return func()
    def disp( s, fo, cb ):
        b_en = Gtk.CheckButton( 'en' )
        r = [ b_en ]
        if fo.en:
            b_en.set_active( True )
            bt = Gtk.CheckButton( 'volatile' )
            bt.connect('clicked', fo.update_cb, 'volatile')
            r.append( bt )
        b_en.connect('clicked', fo.update_cb, 'en', fo._p.update_all)
        return r

class objsel( xml_storable ):
    def __init__( s ):
        pass
    def setup_obj( s, btn ): # TODO: handle error, show result ?
        o = s._p
        o.get( s.path+'/'+s.n ).load_cfg( s.cn )
        o.update_all()
    def gen_setup( s ):
        o = s._p.get( s.path+'/'+s.n )
        if hasattr( o, 'gen_setup' ):
            o.gen_setup()
    def disp( s, o, n, b ):
        bb =  Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        b.add( bb )
        b = bb
        sel_o = o.get( s.path )
        l = []
        for n,i in sel_o.__dict__.items():
            if isinstance( i, s.sc ) and not n.startswith( '_' ):
                l.append( ( i.n, n ) )
        b.add( gen_combo( o, n, l, o ) )
        try:
            so = sel_o.get( s.sel )
            act_cfg = getattr( so, 'cfg_name', '?' )
            if not act_cfg == s.cn:
                b.add( Gtk.Label( 'actual config: ' + act_cfg ) )
                bst = Gtk.Button( 'Set config: ' + s.cn )
                bst.connect( 'clicked', s.setup_obj )
                b.add( bst )
        except AttributeError as e:
            pass

