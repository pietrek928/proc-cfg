#!/usr/bin/python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository.Gdk import color_parse

class xml_storable:
    def store_array( s, e, a ):
        e.attrib[ 't' ] = 'xml_array'
        for i in a:
            ee = Et.SubElement( e, 'a' )
            s.store_obj( ee, i )

    def load_array( s, e ):
        return [ s.load_obj(ee)
                for ee in e.findall( 'a' ) ]

    def store_dict( s, e, a ):
        e.attrib[ 't' ] = 'xml_dict'
        for n,i in a.items():
            ee = Et.SubElement( e, n )
            s.store_obj( ee, i )

    def load_dict( s, e ):
        return { ee.tag:s.load_obj(ee)
                for ee in e }


    def store_obj( s, e, o ):
        if type(i) in ( str, int ):
            e.attrib[ 'v' ] = str( i )
        elif type(o) in ( list, tuple ):
            e.attrib[ 't' ] = 'xml_array'
            s.store_array( e, o )
        elif type(o) in ( dict ):
            e.attrib[ 't' ] = 'xml_dict'
            s.store_dict( e, o )
        else:
            try:
                o.xml_store( e )
            except KeyError:
                pass

    def load_obj( s, e ):
        t = e.get('t')
        if t is None:
            try:
                r = ee.attrib['v']
                r = int( v )
            except ValueError:
                pass
            return r
        elif t == 'xml_array':
            return s.load_array( e )
        elif t == 'xml_dict':
            return s.load_dict( e )
        else: # TODO: where to look for classes ?
            return globals()[t]().xml_load( e )

    def xml_store( s, e ):
        e.attrib[ 't' ] = s.;
        for n,v in s.__dict__.items():
            if not n.startswith('_'):
                ee = Et.SubElement( e, n )
                s.store_obj( ee, v )
    def xml_load( s, e ):
        for ee in e:
            setattr( s, ee.tag, s.load_obj( ee ) )
        return s


def change_list_cb( cb, o, n, parent_obj=None ):
    model = cb.get_model()
    index = cb.get_active()
    setattr( o, n, model[index][-1] )
    if not (parent_obj==None): parent_obj.update_all()

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
        o = s
        for i in l.split( '/' ):
            if i.startswith( '.' ):
                if i == '..':
                    o = o.p
                elif i == '...':
                    o = o.cfg
                #elif i == '.$':
                else:
                    raise ValueError( 'invalid path command: \'%s\'' % str(i) )
            else:
                o = getattr( o, i )

    def go( s, t ):
        o = s
        for i in t:
            if i.startswith( '.' ):
                if i == '..':
                    o = o.p
                elif i == '...':
                    o = o.get_cfg()
                #elif i == '.$':
                else:
                    raise ValueError( 'invalid path command: \'%s\'' % str(i) )
            else:
                o = getattr( o, i )
    def unlink( s, l ):
        t = l.split('/')
        o = s.go( t[:-1] )
        v = getattr( o, t[-1] )
        try:
            v.remove()
        except AttributeError:
            pass
        delattr( o, t[-1] )

    def set( s, l, v ):
        t = l.split('/')
        o = s.go( t[:-1] )
        try:
            getattr( o, t[-1] ).remove()
        except AttributeError:
            pass
        setattr( o, t[-1], v )

    def get_obj_list( s, t ):
        o = s.p
        o = s.get()
        r = []
        for n,i in o.__dict__.items():
            if isinstance( i, t ):
                r.append( ( n, t.n ) )
        return r

class config_descr:
    def __init__( s, d, tt, ff=[] ):
        s.d = d
        s.tt = tt
        s.ff = ff

# o: object that contains variable
# n: variable name
# f: option list, tuple: ( descr, value )
# parent_obj: object that receives change event
def gen_combo( o, n, f, parent_obj=None ):
    ee = f[0]
    ii = 0
    _ii = 0
    vv = None
    if hasattr(o,n): vv=getattr(o,n)
    if isinstance( ee, tuple ):
        names = Gtk.ListStore( type(ee[0]), type(ee[1]) )
        for a in f:
            names.append( [ a[0], a[1] ] )
            if a[0] == vv: ii=_ii
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
    cb.connect("changed", change_list_cb, o, n, parent_obj)
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
        if hasattr( s, 'update_val' ): s.update_val()
        if s.editing():
            b = s.show( )
            b.show_all()

    def editing( s ):
        return hasattr( s, '_pb' )

    def close( s ):
        delattr( s, '_pb' )

    def rollup( s ):
        if hasattr( s, '_pb' ):
            pb = s._pb
            for c in pb.get_children():
                pb.remove( c )

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
        except KeyError,AttributeError:
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
"        for i in cd.tt:
            f = i.fv
            n = i.n
            if hasattr( cc, n ):
                tt = type( vv )
                if tt in ( int, str ):
                    setattr( s, n, vv )
                else:
                    setattr( s, n, tt.cset(vv) )
            else:
                try:
                    delattr( s, n )
                except AttributeError:
                    pass #"

    def parent_set_cb( s, c, p ):
        if not c.get_parent():
            s.close()

    def hasopt( s, n ):
        return hasattr( s, n ) and getattr( s, n )

    def descr_short( s ):
        r = ''
        for i in s.__dict__.items():
            if hasattr( i, 'descr_line' )
                r += e.descr_line()
                r += '\n'
        return r

    def show( s ): #TODO: box instead of window ?
        if s.editing():
            s.rollup()
        else:
            s._pb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            s._pb.connect( 'parent-set', s.parent_set_cb )
        pb = s._pb
        cd = s.get_descr_class()
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
                if isinstance( f, list ):
                    b.add( gen_combo( s, n, f, parent_obj=( s if i.up() else None ) ) )
                elif isinstance( f, str ):
                    if f == 'func':
                        b_en = Gtk.CheckButton( 'en' )
                        b.add( b_en )
                        if hasattr( s, n ):
                            b_en.set_active( True )
                            cb = Gtk.CheckButton( 'volatile' )
                            cb.connect('clicked', s.check_func_cb, n, 'volatile')
                            b.add( cb )
                        b_en.connect('clicked', s.check_func_cb, n, 'en')
                    elif f == 'bool':
                        pass
                else:
                    if not hasattr( f, n ):
                        setattr( f, n, f.cfg() )
                    f.disp( s, n, b )
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
        return pb

    def tree_node( s, t, p ):
        tn = t.append( p, [ i.n, s ] ) # TODO: icon
        s.tree_node = tn

class freq( xml_storable ):
    def __init__( s):
        pass
    def disp( s, o, n, b ):
        if not hasattr( o, n ): setattr( o, n, freq_cfg() )
        fo = getattr( o, n )
        fo.update( o, s.l )
        b.add( Gtk.Label( 'X' ) )
        if isinstance( s.mul, list ):
            b.add( gen_combo( fo, 'mul', s.mul, o ) )
        b.add( Gtk.Label( '/' ) )
        if isinstance( f.div, list ):
            b.add( gen_combo( fo, 'div', s.div, o ) )
        b.add( Gtk.Label( '= '+cnv_num( fo.freq )+'Hz' ) )
    def update( s, o, l ):
        src_freq = float( o.get(l) )
        s.freq = src_freq*float(s.mul)/float(s.div)

class input( xml_storable ):
    def __init__( s, n, vd, fv, sl, update=False, pdescr=None ):
        s.n = n
        s.vd = vd
        s.fv = fv
        s.sl = sl
        if update: s.update = update
        if pdescr: s.pdescr = pdescr

    def up( s ):
        return ( hasattr(s,'update') and s.update )


class func( xml_storable ):
    def __init__( s ):
        s.en = False
    def update_cb( s, cb, o, nc ):
        v = cb.get_active()
        setattr( s, nc, v )
        if nc == 'en':
            o.update_all()
    def disp( s, o, n, b ):
        b_en = Gtk.CheckButton( 'en' )
        b.add( b_en )
        if hasattr( s, n ):
            b_en.set_active( True )
            cb = Gtk.CheckButton( 'volatile' )
            cb.connect('clicked', getattr( o, n ).update_cb, o, 'volatile')
            b.add( cb )
        b_en.connect('clicked', getattr( o, n ).update_cb, o, 'en')

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

