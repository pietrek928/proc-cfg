#!/usr/bin/python

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import Pixbuf
from sys import modules
#from gi.repository.Gdk import color_parse
import xml.etree.ElementTree as Et
import traceback

ld_base = {
    's': str,
    'i': int,
    'f': float,
    'b': bool
}
ld_base_r = dict( tuple(reversed(i))
                for i in ld_base.items() )

def flush_children( o ):
    for i in o.get_children():
        o.remove( i )

def _xml_store( fl, e ):
    for n,v in fl:
        if not n.startswith('_'):
            if isinstance( v, str ):
                e.attrib[n] = v
            else:
                ee = Et.SubElement( e, n )
                _store_obj( ee, v )

def _xml_load( e, cm ):
    return ([ (n,str(i)) for n,i in e.attrib.items() if not n.startswith('_') ]
            + [ (ee.tag, _load_obj( ee, cm )) for ee in e ])

dmod = modules[list.__module__]

def _load_obj( e, cm ):
    t = e.get('_')
    if t in ld_base:
        return ld_base[t]( e.attrib['v'] )
    else:
        try:
            r = getattr(cm, t)()
        except (KeyError, AttributeError):
            r = getattr(dmod, t)()
        try:
            r = r.xml_load( e, cm )
        except (KeyError, AttributeError):
            if isinstance( r, dict ):
                r.update( _xml_load( e, cm ) )
            else:
                try:
                    r.extend( list(zip( _xml_load( e, cm ) ))[1] )
                except IndexError:
                    pass
        return r

def _store_obj( e, o ):
    t = type(o)
    if t in ld_base_r:
        e.attrib[ '_' ] = ld_base_r[t]
        e.attrib[ 'v' ] = str( o )
    else:
        try:
            e.attrib[ '_' ] = type(o).__name__;
            o.xml_store( e )
        except (KeyError, AttributeError):
            if isinstance( o, dict ):
                _xml_store( o.items(), e )
            else:
                _xml_store( zip(['l']*len(o),o), e )

def load_file( fn, cm ):
    e = Et.parse( fn ).getroot()
    r = _load_obj( e, cm )
    r.fix_parent()
    return r

class xml_storable:
    def store_file( s, fn, n='eeelo' ):
        p = Et.Element( n )
        _store_obj( p, s )
        Et.ElementTree( p ).write( fn )

    def fix_parent( s ):
        for n,i in s.__dict__.items():
            if not n.startswith('_'):
                try:
                    i._p = s
                    i._n = n
                    i.fix_parent()
                except (KeyError, AttributeError):
                    pass

    def xml_load( s, e, cm ):
        s.__dict__.update( _xml_load( e, cm ) )
        return s
    def xml_store( s, e ):
        _xml_store( s.__dict__.items(), e )

    def cp( s ):
        r = s.__class__()
        r.__dict__.update({
            n:v for n,v in s.__dict__items
                if not n.startswith('_')
        })
        return r

def vset_cb( o, n, cb=None ):
    if cb:
        def r(v = None):
            if v is not None:
                setattr(o, n, v)
            cb()
    else:
        def r(v = None):
            if v is not None:
                setattr(o, n, v)
    return ( getattr(o, n, None), r)

def iconview_tp_cb( iv, x, y, kbd, tp ):
    try:
        p = iv.get_path_at_pos( x, y )[0]
        m = iv.get_model()
        e = m.get_value( m.get_iter( p ), 0 )
        tp.set_text( e.get_tooltip() )
        iv.set_tooltip_cell( tp, p )
    except (AttributeError, TypeError):
        return False
    return True

def iconview_ac_cb( iv, p ):
    m = iv.get_model()
    e = m.get_value( m.get_iter( p ), 0 )
    e.show_window() # TODO: callback
    return True

def treeview_tp_cb( tv, x, y, kbd, tp ):
    try:
        p = tv.get_path_at_pos( x, y )[0]
        m = tv.get_model()
        e = m.get_value( m.get_iter( p ), 0 )
        tp.set_text( e.get_tooltip() )
        tv.set_tooltip_row( tp, p )
    except (AttributeError, TypeError):
        return False # TODO: debug
    return True

def treeview_exp_cb( tv, it, p ):
    try:
        m = tv.get_model()
        e = m.get_value( it, 0 )
        n = m.iter_n_children( it )
        e.tload( m, it )
        ci = m.iter_children( it )
        while n and m.remove( ci ):
            n -= 1
    except (AttributeError, TypeError) as e:
        print('treeview_exp_cb: ', e)
        return False # TODO: debug
    return True

def treeview_col_cb( tv, it, p ):
    try:
        m = tv.get_model()
        e = m.get_value( it, 0 )
        ci = m.iter_children( it )
        while m.remove( ci ):
            pass
        e.tload_def( m, it )
    except (AttributeError, TypeError) as e:
        return False # TODO: debug
    return True

def treeview_act_cb( tv, p, c, cb ):
    try:
        m = tv.get_model()
        e = m.get_value( m.get_iter( p ), 0 )
        tv.expand_row( p, False )
        cb( e )
    except (AttributeError, TypeError) as e:
        print('treeview_act_cb', e)
        return False # TODO: debug
    return True

def treeview_sel_cb( tv, cb ):
    try:
        p,c = tv.get_cursor()
        m = tv.get_model()
        e = m.get_value( m.get_iter( p ), 0 )
        cb( e )
    except (AttributeError, TypeError) as e:
        print('treeview_sel_cb: ', e)
        return False # TODO: debug
    return True

def view_btn_cb( tv, ev ):
    try:
        p = tv.get_path_at_pos( ev.x, ev.y )[0]
        m = tv.get_model()
        e = m.get_value( m.get_iter( p ), 0 )
        e.call_act( e )  # TODO: different action depending on widget
        return True
    except (KeyError, AttributeError, TypeError) as e:
        print('view_btn_cb: ', e) #TODO: error logger
        pass

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

class param_set:
    class param:
        def __init__(s, n, v=None, isp=None):
            s.n = n
            s.v = v
            s.isp = isp
        def val(s, o, d):
            n = s.n
            try:
                return d[n]
            except KeyError: # TODO: name of param inside function
                try:
                    return getattr(o, n)
                except AttributeError:
                    v = s.v
                    try: # TODO: type, link ?
                        return (getattr( o, v[1:], None ) if v.startswith('$') else v)
                    except AttributeError:
                        return v
        def fp( s ):
            return '{} {}'.format(s.t, s.n)
    def __init__( s, *p ):
        s.p = [s.param(*i) for i in p]
    def scall( s, o, d ):
        return dict( p.val(o, d) for p in s.p)
    def sdecl( s, o, d ):
        return { p.n:( p.n if p.isp else p.val(o, d)) for p in s.p}
    def decl( s ):
        l = []
        return ','.join([ p.fp() for p in s.p if p.isp ])
    def call( s, o, d ):
        return ','.join([ p.val(o, d) for p in s.p if p.isp ])

def setup_params( *params ):
    ps = param_set( *params )
    def decor( f ):
        def r( s, *a, **args ):
            s._S = ps.sdecl( s, args )
            return f( s, *a )
        return r
    return decor

def gen_func( *params, rt='void' ): # TODO: name prefix ? object, class, namespace ?
    def decor( f ):
        def r( s, **args ): # c / c++ selection ?
            ps = param_set( *params )
            ln = s.wctx().ln
            try:
                c = getattr( s, '_fcfg_'+f.__name__ )
            except AttributeError:
                c = func() # blank func config
                setattr( s, '_fcfg_'+f.__name__, c ) # TODO: fixing parameter function
            fn = '{}_{}'.format( s.n, f.__name__ ) # TODO: put func in class ?
            if args.get('decl',None): # TODO: ctx for ln
                ln('{} {}({}) {{', # TODO: attrs ?
                    rt, fn, ps.decl()
                )
                s._S = ps.sdecl( s, args )
                rn = f( s )
                if rt != 'void':
                    ln('return {};', rn)
                ln('}}')
            else:
                if not c.en:
                    print('function {} is used but not enabled'.format(fn)) # FIXME: warn
                inl = args.get('inline',None) or getattr(c, 'inline', None)
                if not inl:
                    try:
                        v = ps.call( s, args ) # TODO: multiple func versions
                    except ValueError:
                        inl = True
                if inl:
                    s._S = ps.scall( s, args ) # TODO: local vars
                    rf = f( s ) # TODO: conversion ? return type ?
                elif v is not None:
                    rf = '{}({})'.format(fn,v)
                else: # TODO: warn
                    raise ValueError('invalid arguments')
                if rf is not None:
                    if rt != 'void' and args.get('rn', None):
                        ln('{} {} = {};', rt, args['rn'], rf)
                        return rn
                    else:
                        ln('{};', rf)
        return r
    return decor



link_func = {
        '.': lambda o: o,
        '..': lambda o: o._p,
        '...': lambda o: o.go_proc()
}
class link_path: # TODO: move to config_parent ?
    # def _get( s, t ):
        # try:
            # t.reverse()
            # while t:
                # i = t.pop()
                # if i.startswith( '.' ):
                    # try:
                        # s = link_func[i]( s )
                    # except AttributeError: # TODO: nop default ?
                        # raise NotImplementedError( 'no path command: \'%s\'' % str(i) )
                # else:
                    # try:
                        # s = getattr( s, i )
                    # except AttributeError: # TODO: cut recursion, better error
                        # l = s._l.split('/')
                        # l.reverse()
                        # t.extend( l )
                        # s = s._p
            # FIXME: resolve link at the end of path
            # return s
        # except AttributeError:
            # raise LookupError( 'no path \'{}\''.format( l ) )

    def get( s, l ):
        try:
            t = l.split( '/' )
            t.reverse()
            while True:
                while t:
                    i = t.pop()
                    if i.startswith( '.' ):
                        try:
                            s = link_func[i]( s ) # call a standard path function
                        except KeyError:
                            try:
                                s = getattr( s, i )() # call a custom function from object
                            except (AttributeError, TypeError):
                                raise NotImplementedError('no path command: \'{}\''.format(i) ) # TODO: allow call a method here ?
                    else:
                        try:
                            s = getattr( s, i )
                        except AttributeError: # TODO: cut recursion
                            t.append( i ) # try to get it once more
                            t.extend( reversed( s._l.split('/') ) ) # TODO: lazy load here ?
                            s = s._p
                if hasattr( s, '_l' ): # go further if found a link
                    t = s._l.split('/') # TODO: lazy load here ?
                    t.reverse()
                    s = s._p
                else:
                    return s
        except AttributeError:
            raise LookupError( 'path \'{}\' not found'.format( l ) ) # FIXME: search for debug info ?

    def get_dep( s, l, p ): # !!!!!!!!!!!!
        try:
            t = l.split( '/' )
            t.reverse()
            while t:
                i = t.pop()
                if i.startswith( '.' ):
                    try:
                        s = link_func[i]( s )
                    except AttributeError: # TODO: nop default ?
                        raise NotImplementedError( 'no path command: \'%s\'' % str(i) )
                else:
                    try:
                        s = getattr( s, i )
                    except AttributeError: # TODO: cut recursion, better error
                        l = s._l.split('/')
                        l.reverse()
                        t.extend( l )
                        s = s._p
                if s._p is p: return s
                # FIXME: resolve link at the end of path
        except AttributeError:
            raise LookupError( 'no path \'{}\''.format( l ) )

    def unlink( s, l ):
        t = l.split('/')
        o = s._get( t[:-1] )
        n = t[-1]
#        try:
#            getattr( o, n ).remove()
#        except AttributeError:
#            pass # TODO: log ?
        delattr( o, n )

    def set( s, l, v ):
        t = l.split('/')
        o = s._get( t[:-1] )
        n = t[-1]
#        try: # perform remove first ?
#            getattr( o, n ).remove()
#        except AttributeError:
#            pass
        setattr( o, n, v )

    def get_obj_list( s, l, t ):
        return [ ( n, i.n ) for n,i in s.get(l).__dict__.items()
                if i.__class__.__name__.startswith( t ) ]

    def get_path( s ):
        try:
            return '{}/{}'.format( s._n, s._p.get_path() )
        except AttributeError:
            return ''

    # def v( s ):
        # while hasattr( s, '_l' ):
            # s = s.get( s._l )
        # return s

    def link_reconfigure( s, l, c ):
        t = l.split('/')
        o = s._get( t[:-1] )
        o.child_reconfig( c, t[-1] )

class config_descr:
    def __init__( s, d, tt, ff=[] ):
        s.d = d
        s.tt = tt #[ input_descr( *i ) for i in tt ]
        s.ff = ff

def change_combo_cb( cb, cbk ):
    model = cb.get_model()
    index = cb.get_active()
    cbk( model[index][-1] )

def change_checkbox_cb( b, cb ):
    cb(b.get_active())

# f: option list, tuple: ( descr, value )
# v: current value
# cbk: setter callback
def gen_combo( f, v, cbk ):
    try:
        fo = f
        if hasattr( f, 'dl' ):
            f = list( f.dl() )
        ee = f[0]
        if not isinstance(ee, tuple):
            f = tuple([i] for i in f)
            ee = f[0]
        names = Gtk.ListStore(*[type(i) for i in list(ee)])
        for a in f:
            names.append( list( a ) )
        try:
            pos = fo.index(v)
        except:
            pos = 0
            cbk( ee[-1] )
        cb = Gtk.ComboBox.new_with_model(names)
        cb.set_active( pos )
        r = Gtk.CellRendererText()
        cb.pack_start(r, True)
        cb.add_attribute( r, 'text', 0 )
        cb.connect("changed", change_combo_cb, cbk)
        return cb
    except Exception as e:
        print('gen_combo: ', e)
        return Gtk.Box()

def gen_proc_view( t ): # to render
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

    ev_act = { # type, button, state(func keys)
            (Gdk.EventType.BUTTON_PRESS, 3, 0) : lambda e, ev: e.menu().popup_at_pointer( ev )
    }

    def call_act( s, e, w=None, c=None ):
        try:
            t = (e.type, e.button, e.state)
            act = (ev_act.get(t, None)
                   or ev_act.get((*t, w), None)
                   or ev_act.get((*t, c), None)
                   or ev_act.get((*t, w, c), None)
            )
            act( s, e )
        except (KeyError, AttributeError, TypeError) as e:
            pass

    def get_icon( s ):
        return getattr( s, 'icon', 'edit-copy' )

    def has_val( s, n, v ):
        return getattr( s, n, None ) == v

    def go_proc( s ):
        try:
            while not hasattr( s, 'proc_cfg' ): s = s._p
        except (AttributeError,KeyError):
            return None
        return s

    def get_cfg( s, n ): # TODO: cache
        try:
            while not hasattr( s, n ): s = s._p
        except (AttributeError,KeyError):
            return None
        return getattr( s, n )

    def get_root( s ):
        try:
            while not hasattr( s, '_r' ): s = s._p
        except (AttributeError,KeyError):
            return None
        return s

    def get_arg( s, n ):
        try:
            return s._S[n]
        except (AttributeError, KeyError):
            return getattr( s, n )

    @gen_func()
    def gen_setup( s ):
        for i in s.__dict__.values():
            if hasattr(i, 'gen_setup') and getattr(i, 'en', None):
                i.gen_setup()

    def imported( s ):
        for n,i in s.__dict__.items():
            if not n.startswith('_'):
                try:
                    i._p = s
                    i.imported()
                except AttributeError:
                    pass

    def clr( s ):
        d = s.__dict__
        l = []
        for n,i in d.items():
            if n.startswith( '_' ):
                l.append( n ) # cant delete during iteration
            elif hasattr( i, 'clr' ):
                i.clr()
        for n in l:
            del d[n]

    def find_deps( s, p ):
        r = set() #{ s.get_dep( l, s ) for l in s.deps() }
        for n, i in s.__dict__.items():
            if not n.startswith('_'):
                try:
                    r |= i.find_deps( p )
                except AttributeError:
                    pass
        return r

    # returns child names in dependency order
    def find_child_order( s ): #TODO: dependency cache
        d = {}
        od = {}
        e = { i for n,i in s.__dict__.items() if hasattr( i, 'find_deps') and not n.startswith('_') }
        for n,i in s.__dict__.items():
            try:
                if i in e:
                    d[i] = i.find_deps( s ) & e
                    od[i] = n
            except (AttributeError, TypeError):
                pass
        r = []
        t = [ o for o,i in d.items() if not i ]
        while t:
            t2 = []
            for i in t:
                l = d[i]
                r.append(od[i])
                for j in l:
                    dd=d[j]
                    dd.discard(i)
                    if not dd:
                        t2.append(i)
            t=t2
        for o,dd in d.items():
            if dd:
                # TODO: dependency cycle warning
                r.append( od[o] )
        return r

    def _check_links( s, d ):
        for n,i in s.__dict__.items():
            try:
                if hasattr(i, '_l'):
                    d.setdefault(s.get(i._l),[]).append(i)
            except LookupError:
                print( 'WARNING: broken link {}'.format(i.get_path()) ) # TODO: error, warning log
                pass # TODO: log broken link
            try:
                i._check_links( d )
            except AttributeError:
                pass

    def check_links( s ):
        d = {}
        s._check_links( d )
        for o, l in d.items():
            if len(l) >= 2: # TODO: multiple option in links
                print( 'WARNING: multiple reference to {} from:'.fromat(o.get_path()) ) # TODO: error log, console ?
                print( '\n'.join(['    {}'.format(i.get_path()) for i in l]) )

    def wctx( s ):
        try:
            return s._wctx
        except AttributeError:
            r = s._p.wctx()
            s._wctx = r
            return r

    def get_tooltip( s ):
        if not hasattr( s, 'descr_short' ): return s.n
        return s.descr_short()

    def show_window( s ):
        w = Gtk.Window()
        w.set_title( getattr( s, 'name', s.n ) )
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        w.add( b )
        b.add( s.render('fields') )
        b.add( s.render('tiles') )
        w.show_all()
        return w

    def del_child( s, n ):
        try:
            e = getattr( s, n )
            delattr( s, n )
            e.remove()
        except ( KeyError, AttributeError ):
            pass

    def remove( s ): #TODO: list ?
        for n,i in s.__dict__.items():
            if hasattr( i, 'remove' ) and not n.startswith( '_' ):
                i.remove()

    def cp( s ):
        r = s.__class__()
        for n, v in s.__dict__.items():
            if not n.startswith('_'):
                try:
                    o = v.cp()
                except AttributeError:
                    o = v;
            setattr( r, n, o )
        return r

    def default_name( s, o=None ):
        n = s.__class__.__name__
        if not o: return n
        n += '_'
        i = 1
        while hasattr( o, n+str(i) ):
            i+=1
        return n+str(i)

    def clk_start( s ):
        s.get_cfg('cstart')( s.clk_name() )

    # returns loaded config
    def load_cfg( s, n ):
        return s.get_cfg( 'import_cfg' )( n )

    def child_reconfig( s, c, n=None ):
        if isinstance( c, str ):
            c = s.load_cfg( c )
        if not n:
            n = c.default_name( s ) # !!!!
        try:
            v = getattr( s, n )
            if v.__class__ is c.__class__: # FIXME: must be strict comparison ?
                v.reconfigure( c )
            else:
                raise AttributeError # copy obj in except
        except AttributeError:
            c = c.cp() # FIXME: what if no cp ?
            setattr( s, n, c )
            try:
                c._p = s
                c.imported()
            except AttributeError:
                pass

    def reconfigure( s, c ):
        for n,i in c.__dict__.items():
            if not n.startswith( '_' ):
                try:
                    v = getattr( s, n )
                    if v.__class__ is i.__class__:
                        v.reconfigure( i )
                    else:
                        setattr( s, n, i )
                except AttributeError:
                    setattr( s, n, i )
        # FIXME: remove other params ? option ?

    def expander_cb( s, e ):
        if not e.get_expanded():
            if not s.editing():
                e.add( s.show() )
                e.show_all()
        else:
            #flush_children( e )
            for i in e.get_children():
                if isinstance( i, Gtk.Box ):
                    e.remove( i )

    def iv_drag_recv( s, iv, ctx, x, y, sel, info, tm ):
        p, m = iv.get_dest_item_at_pos( x, y )
        if not p: return False
        p = int(p.to_string())
        if m == Gtk.IconViewDropPosition.DROP_RIGHT: p+=1
        m = iv.get_model()
        e = m.get_value( m.get_iter( str(p) ), 2 )
        print('recv',p,e)
        s.child_reconfig( e )
        s.find_child_order()
        #tp.set_text( e.get_tooltip() )
        #iv.set_tooltip_cell( tp, pp )
        return True

    def iv_drag_get( s, iv, ctx, sel, info, tm ):
        p = iv.get_selected_items()[0]
        if not p: return False
        print('path',p)
        m = iv.get_model()
        e = m.get_value( m.get_iter(p), 2 )
        print( 'get', e.n )
        #tp.set_text( e.get_tooltip() )
        #iv.set_tooltip_cell( tp, pp )
        return True

    def hasopt( s, n ):
        return hasattr( s, n ) and getattr( s, n )

    def descr_short( s ):
        r = ''
        for i in s.__dict__.values():
            if hasattr( i, 'descr_line' ):
                r += e.descr_line()
                r += '\n'
        return r

    def get_exp( s ):
        return [ i for i in s.__dict__.values()
                if hasattr( i, 'expander_cb' ) ]

    def get_ivs( s ):
        return [ i for i in s.__dict__.values()
                if hasattr( i, 'iv_data' ) ]

    def parent_set_cb( s, c, p, n ):
        if not c.get_parent():
            s.close( n )

    def close( s, n ):
        try:
            del s._v[n]
        except (AttributeError, KeyError):
            pass

    def update_all( s ):
        try:
            s.update()
        except AttributeError:
            pass
        vd = s.__dict__.setdefault('_v', {})
        for n, o in vd.items():
            try:
                pb = o['pb']
                flush_children( pb )
                getattr( s, 'render_'+n )( pb, *o['p'], **o['pv'] )
                pb.show_all();
            except (KeyError, AttributeError):
                pass

    def create_box( s, opt ): # TODO: options
        if opt.get('type', None) == 'scroll':
            b = Gtk.ScrolledWindow()
        else:
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        return b

    def render( s, vn, *p, **pv ):
        try:
            vd = s.__dict__.setdefault('_v', {})
            try:
                o = vd[vn]
                del vd[vn]
                getattr( s, 'hide_'+vn )( o['pb'], *o['p'], **o['pv'] )
            except (KeyError, AttributeError):
                pass
            #pb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL) TODO: scrolled window with box ?
            #pb.connect( 'parent-set', s.parent_set_cb )
            r = s.create_box(pv.get('box_opt', {}))
            r.connect( 'parent-set', s.parent_set_cb, vn )
            getattr( s, 'render_'+vn )( r, *p, **pv )
            r.show_all();
            vd[vn] = {'pb':r, 'p':p, 'pv':pv}
            return r
        except KeyError:
            print('No render {} for {} object'.format(vn,s.__class__.__name__))
            return None

    def render_tree( s, pb=None, sel_cb=None, act_cb=None ):
        ts = Gtk.TreeStore(object, str)
        s.trow( ts, None )

        tv = Gtk.TreeView(model=ts)
        tv.append_column(
                Gtk.TreeViewColumn('Name', Gtk.CellRendererText(), text=1)
        )
        tv.set_headers_visible(False) # FIXME header breaks get_path_at_pos
        tv.set_property( 'has-tooltip', True )
        #tv.set_property( 'hover-expand', True )
        tv.connect( 'query-tooltip', treeview_tp_cb )
        tv.connect( 'row-expanded', treeview_exp_cb )
        tv.connect( 'row-collapsed', treeview_col_cb )
        # tv.connect( 'expand-collapse-cursor-row', treeview_cur_exp_cb ) # TODO: left, right in css
        tv.connect( 'button-press-event', view_btn_cb )
        if sel_cb: tv.connect( 'cursor-changed', treeview_sel_cb, sel_cb )
        if act_cb: tv.connect( 'row-activated', treeview_act_cb, act_cb )
        pb.add(tv)

    def render_fields( s, pb=None, show_tiles=False ): # TODO: some renderers
        cd = s.descr
        o = s.__dict__
        def frender( n, vd, f, sl={}, od={} ):
            u = not sl
            for a,v in sl.items():
                if a in o:
                    a = o[a]
                    if isinstance( v, tuple ):
                        if a in v: u = True
                    elif a == v: u = True
            if u:
                cbk = vset_cb(s, n, od.get('update', None)
                                and s.update_all)[1] # TODO: update signal instead
                b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                pb.add( b )
                b.add( Gtk.Label( vd ) )
                if isinstance( f, tuple ):
                    f = select_field(*f)
                # elif isinstance( f, str ):
                    # pass
                # else:
                if True:
                    d = o.get( n, None )
                    if d is None:
                        d = f.dv()
                        try:
                            d._p = s
                        except AttributeError:
                            pass
                        o[n] = d
                    l = f.disp( d, cbk )
                    if isinstance(l, list):
                        for c in l: b.add( c )
                    else: b.add(l)
            elif n in o: del o[n]
        for i in cd.tt:
            frender( *i )
        pb.show_all()

    def render_tiles( s, pb=None ):
        if not hasattr( s, 'child_order' ): # TODO: support links here ?
            s.child_order = s.find_child_order() # xml_list( [ n for n,i in d if isinstance( i, config_parent ) ] )
        d = s.__dict__

        il = Gtk.ListStore( object, str, Pixbuf )
        iv = Gtk.IconView()
        iv.set_model( il )
        iv.set_pixbuf_column( 2 )
        iv.set_text_column( 1 )
        for n in s.child_order:
            try:
                i = d[n]
                pixbuf = Gtk.IconTheme.get_default().load_icon(i.get_icon(), 64, 0) # TODO: icon from class
                il.get_path( il.append([i, i.n, pixbuf]) )
            except AttributeError:
                pass
        iv.set_property( 'has-tooltip', True )
        iv.connect( 'query-tooltip', iconview_tp_cb ) # TODO: method from class
        iv.connect( 'item-activated', iconview_ac_cb )
        iv.connect( 'drag-data-get', s.iv_drag_get )
        iv.connect( 'button-press-event', view_btn_cb )
        targets = Gtk.TargetList.new([])
        targets.add_image_targets(1, True)
        iv.enable_model_drag_source( Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.MOVE )
        iv.drag_source_set_target_list( targets )
        if s.hasopt('tiles_edit'):
            iv.enable_model_drag_dest( [], Gdk.DragAction.MOVE )
            iv.drag_dest_set_target_list( targets )
            iv.connect('drag-data-received', s.iv_drag_recv )
            iv.connect('drag-data-delete', lambda *x: (print('delete',*x) or True) )
        pb.add( iv )

    def render_elist( s, pb=None ):
        if not hasattr( s, 'child_order' ): # TODO: support links here ?
            s.child_order = s.find_child_order()
        for n in s.child_order:
            i = d[n]
            e = Gtk.Expander( label=getattr( i, 'name', i.n ) )
            e.connect( 'activate', i.expander_cb )
            pb.add( e )

    def trow( s, t, p ):
        tn = t.append( p, [ s, s.n ] ) # TODO: icon, update row ?
        s.tload_def( t, tn )

    def tload_def( s, t, tn ):
        t.append( tn, [ None, 'Loading...' ] ) # TODO: remember expanded

    def tload( s, t, tn ):
        for i in s.__dict__.values():
            try:
                i.trow( t, tn )
            except AttributeError:
                pass

    def menu( s ):
        m = Gtk.Menu()
        m.append(Gtk.ImageMenuItem("Yep it works!"))
        m.append(Gtk.ImageMenuItem(":)"))
        m.show_all()
        return m

class link( xml_storable ):
    def __init__( s ):
        s._l = '.' # TODO: _this reference ?
    def cp( s ):
        r = super().cp()
        if hasattr( s, '_l' ):
            r._l = s._l
        if hasattr( s, '_cfg' ):
            r._cfg = s._cfg
        return r
    def find_deps( s, p ):
        return { s._p.get_dep( s._l, p ) }
    def gen_setup( s ):
        o = s._p.get( s.l )
        try:
            o.gen_setup()
        except AttributeError:
            pass
    def imported( s ):
        try:
            c = s._p.load_cfg( s._cfg )
            s._p.link_reconfigure( s._l, c ) # TODO: what if exists ?
        except AttributeError:
            pass
    def reconfigure( s, c ): # TODO: configure action/rules
        l = s._l
        if hasattr( c, 'cfg_name' ):
            c = s._p.load_cfg( c.cfg_name )
            s._p.link_reconfigure( l, c )
        else:
            s.set( s._l, c ) # TODO: copy config ?
    def xml_store( s, e ):
        try:
            e.attrib[ 'l' ] = s._l
            e.attrib[ 's' ] = s._s
            # _cfg
        except AttributeError:
            pass
    def xml_load( s, e, cm ):
        try:
            s._l = e.attrib[ 'l' ]
            s._s = e.attrib[ 's' ]
        except AttributeError:
            pass

class freq( link ):
    def __init__( s ):
        super().__init__()
        s.mul = 1
        s.div = 1
    def update( s ):
        src_freq = s._p.get(s.l)
        s.freq = float(src_freq)*float(s.mul)/float(s.div)

class bool_field:
    def __init__( s ):
        pass
    def obj( s ):
        return False
    def disp( s, fo, cb ):
        b = Gtk.CheckButton()
        b.set_active( fo )
        b.connect('toggled', change_checkbox_cb, cb )

class select_field:
    def __init__(s, *l):
        s.l = l
    def dv(s):
        return s.l[0]
    def disp( s, v, cb ):
        return gen_combo(s.l, v, cb)

class freq_setup:
    def __init__( s, l, mul, div=() ):
        s.__dict__.update(locals())
        del s.s
    def dv( s ):
        r = freq()
        r.l = s.l
        return r
    def disp( s, fo, cb ):
        r = [ Gtk.Label( 'X' ) ]
        if isinstance( s.mul, tuple ):
            r.append( gen_combo( s.mul, *vset_cb( fo, 'mul', cb ) ) )
        r.append( Gtk.Label( '/' ) )
        if isinstance( s.div, tuple ):
            r.append( gen_combo( s.div, *vset_cb( fo, 'div', cb ) ) )
        fo.update()
        r.append( Gtk.Label( '= '+cnv_num( fo.freq )+'Hz' ) )
        return r

class func( xml_storable ):
    def __init__( s ):
        s.en = False
    def update_cb( s, cb, nc, cbk=None ):
        setattr( s, nc, cb.get_active() )
        if cbk: cbk()
    def gen_code( s ):
        getattr( s._p, s._n )( decl=True )
        args.update({n:v(s._p) for n,v in params}) # TODO: comment ?

class func_setup:
    def dv( s ):
        return func()
    def disp( s, fo, cb ):
        b_en = Gtk.CheckButton( 'en' )
        r = [ b_en ]
        if fo.en:
            b_en.set_active( True )
            bv = Gtk.CheckButton( 'volatile' )
            bv.connect('clicked', fo.update_cb, 'volatile')
            r.append( bv )
            bi = Gtk.CheckButton( 'inline' )
            bi.connect('clicked', fo.update_cb, 'inline')
            r.append( bi )
        b_en.connect('clicked', fo.update_cb, 'en', cb)
        return r

class objsel_setup:
    def __init__( s, l, cfgn, cn ):
        s.__dict__.update(locals())
        del s.s
    def dv( s ):
        return link() # FIXME: params to child object ?
    def setup_obj( s, btn, fo ): # TODO: handle error, show result ?
        o = fo._p
        o.link_reconfigure( fo._l, s.cfgn )
        o.update_all()
    def disp( s, fo, cb ):
        b = Gtk.Box( orientation=Gtk.Orientation.HORIZONTAL )
        r = [ b ]
        sel_o = fo._p.get( s.l )
        l = []
        for n,i in sel_o.__dict__.items():
            if i.__class__.__name__.startswith( s.cn ) and not n.startswith( '_' ):
                l.append( ( i.n, n ) )
        b.add( gen_combo( l, *vset_cb( fo, '_s', cb ) ) )
        try:
            fo._l = s.l+'/'+fo._s
            so = fo._p.get( fo._l )
            act_cfg = getattr( so, 'cfg_name', '?' )
            if not act_cfg.startswith( s.cfgn ): # TODO: some object info ?
                b.add( Gtk.Label( 'actual config: ' + act_cfg ) )
                bst = Gtk.Button( 'Set config: ' + s.cn )
                bst.connect( 'clicked', s.setup_obj, fo )
                b.add( bst )
        except AttributeError as e:
            b.add( Gtk.Label( 'no objects to select at {}/'.format( s.l ) ) )
        return r

