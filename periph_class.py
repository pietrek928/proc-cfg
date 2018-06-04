#!/usr/bin/bash

import xml.etree.ElementTree as Et;
from sys import modules

from gui import xml_storable, load_file, _store_obj, _xml_store, _xml_load

class nl( list ):
    def xml_store( s, e ):
        _xml_store([ (i.n,i) for i in s ], e)
        for i in e:
            i.attrib.pop( 'n', None )
    def xml_load( s, e, cm ):
        for n,i in _xml_load( e, cm ):
            i.n = n
            s.append( i )
        return s

class nd( dict ):
    def xml_store( s, e ):
        _xml_store(s.items(), e)
        for i in e:
            i.attrib.pop( 'n', None )
    def xml_load( s, e, cm ):
        for n,i in _xml_load( e, cm ):
            i.n = n
            s[n]=i
        return s

def dict_get_sorted( d, ll ):
    tt = [ *d.values() ]
    tt.sort( key=ll )
    return tt

class reg_bit( xml_storable ):
    def __init__( s ):
        pass
    def set( s, n, a, boff=0 ):
        s.n=n
        b=boff
        bb=None
        while a>0:
            if bb == None:
                if not a&1 == 0: bb=b
            a>>=1
            b=b+1
        s.b = bb
        if not bb==b-1:
            s.e = b-1
    def xml_store( s, e ):
        e.attrib[ 'n' ] = s.n
        e.attrib[ 'b' ] = str( s.b )
        if hasattr( s, 'doc' ):
            e.attrib[ 'doc' ] = s.doc
        if ( hasattr( s, 'e' ) ): e.attrib[ 'e' ] = str( s.e )
    def xml_load( s, *a ):
        super().xml_load( *a )
        s.b = int( s.b )
        if hasattr( s, 'e' ): s.e = int(s.e)
        return s

class struct_field( xml_storable ):
    def __init__( s ):
        s.b = {}
    def make_array( s, n=1 ):
        if hasattr(s,'ne'): return
        s.ne = n
    def size( s ):
        return (s.ne if hasattr(s,'ne') else 1)*s.l
    def join( s, f ):
        s.make_array()
        f.make_array()
        if not s.l == f.l: ValueError('different element sizes')
        off = s.size()*8
        for nn,i in f.b.items():
            i.b += off
            if hasattr( i, 'e' ): i.b += off
            s.b[ nn ] = i
        s.ne += f.ne
        del f
    def xml_store( s, e ):
        if hasattr( s, 'ne' ):
            e.attrib[ 'ne' ] = str( s.ne )
        if not hasattr( s, 't' ):
            e.attrib[ 'l' ] = str( s.l )
        if hasattr( s, 't' ):
            t = s.t
            e.attrib[ 't' ] = ( t if isinstance(t,str) else t.n  )
        if hasattr( s, 'doc' ):
            e.attrib[ 'doc' ] = s.doc
        ee = Et.SubElement( e, 'v' )
        _store_obj( ee, nl( dict_get_sorted( s.b, lambda v: v.b ) ) )
    def xml_load( s, *a ):
        super().xml_load( *a )
        if hasattr( s, 'ne' ): s.ne = int( s.ne )
        if hasattr( s, 'l' ): s.l = int( s.l )
        s.b = {i.n:i for i in s.v}
        return s
    def get_descr( s ):
        try:
            return '{}({})'.format( s.n, s.doc )
        except AttributeError:
            return s.n

class struct_descr( xml_storable ):
    def __init__( s ):
        s.l = 0
        s.t = nl()
    def add( s, f ):
        f.off = s.l
        s.l += f.l
        s.t.append( f )
    def union_fields( s, tp ): # called once for single object
        un = None
        _ot = s.t
        s.t = nl()
        s.l = 0
        for i in _ot:
            if un:
                if ( i.n.startswith( lj[0] ) and i.n.endswith( lj[1] ) ) or hasattr(i,'reserved'):
                    un.join( i )
                else:
                    s.add( un )
                    un = None
            if not un:
                for j in tp:
                    if i.n.startswith( j[0] ) and i.n.endswith( j[1] ):
                        un = i
                        lj = j
                        i.n = j[0]+j[1]
                        break;
                if not un:
                    s.add( i )
        if un: s.add( un )
    def clr( s ):
        if hasattr( s, 'tt' ): delattr( s, 'tt' )
    def update_load( s, p=None ):
        if p:
            for i in s.t:
                if hasattr( i, 't' ):
                    if isinstance( i.t, str ):
                        i.t = p.get_type( i.t )
                    i.l = i.t.l
        s.l = 0
        for i in s.t:
            i.off = s.l
            s.l += i.size()
        s._t = {i.n:i for i in s.t}
    def xml_store( s, e ):
        super().xml_store( e )
        for i in e:
            if i.tag == 'l':
                e.remove( i )
                break

class periph_obj( xml_storable ):
    # def gen_setup( s, out, fn, fl, mode ): # TODO: faster version in C++
        # ln = out.ln
        # f = s.t._t[ fn ]
        # ln('   /* {}: {}  */'.format(f.get_descr(),fl))
        # zu = mode.zu
        # zz = mode.zz
        # if zz: zu=False
        # vv = [0]*f.ne
        # nbits = f.l*8
        # ones = (1<<nbits)-1
        # if zu:
            # uu = [ones]*f.ne
        # for n,v in fl.items():
            # ff = f.b[ n ]
            # nn = ff.b//nbits
            # ss = ff.b %nbits
            # vv[nn] |= int(v)<<ss # TODO: unconstant value
            # if zu and not mode.ww:
                # uu[nn] &= ~(((1<<(1 if not hasattr(ff,'e') else ((ff.e%nbits)-ss+1)))-1)<<ss);
        # fpos = s.a+f.off;
        # pp =( '=' if zz or mode.ww else '|=' ) # preserve previous
        # vol = ( 'volatile ' if mode.vol else '' )
        # for it in range(len(vv)): # TODO: preserve current vals
            # fp = '( *({}uint{}_t*){})'.format(vol, f.l*8, hex(fpos+it*f.l))
            # nv = None
            # av = None
            # if zz or vv[it]!=0:
                # nv = '0x%0*x' % (nbits//4,vv[it])
            # if zu and uu[it]!=just_ones:
                # av = '0x%0*x' % (nbits//4,uu[it])
            # if av and nv:
                # ln('{0}=((({0})&{1})|{2});'.format(fp, av, nv))
            # elif nv:
                # ln(fp+pp+nv+';')
            # elif av:
                # ln('{}&={};'.format(fp, av)) # TODO: negate flag
    def __init__( s ):
        a=0
    def xml_store( s, e ):
        e.attrib['t'] = s.t.n
        e.attrib['a'] = hex(s.a)
    def xml_load( s, e, cm ):
        s.t = e.attrib['t']
        s.a = int(e.attrib['a'],16)
        return s

class proc_cfg( xml_storable):
    def __init__( s ):
        s.clear_data()
    def clear_data( s ):
        s.periph_data = {}
        s.types = nd()
        s.vars = {}
    def import_cfg( s, *n ):
        r = None
        for i in n:
            try:
                c = load_file( f'{s._cfg_dir}/{i}.xml', s._cm )
            except (KeyError, FileNotFoundError):
                c = s._pcfg.import_cfg( i )
            if r:
                r.reconfigure(c)
            else: r=c
        r.cfg_name = n if len(n) else n[0];
        return r
    def get_type( s, n ): # TODO: cache
        try:
            return s.types[ n ]
        except KeyError:
            return s._pcfg.get_type( n )
    def get_periph( s, n ): # TODO: cache
        try:
            return s.periph_data[ n ]
        except KeyError:
            return s._pcfg.get_periph( n )
    def get_var( s, n ): # TODO: cache
        try:
            return s.vars[n]
        except KeyError:
            return s._pcfg.get_var( n )
    def xml_load( s, *a ):
        super().xml_load( *a )
        for n,i in s.types.items():
            i.n = n
            i.update_load( s )
        for n,i in s.periph_data.items():
            s.periph_data[n].t = s.get_type( i.t )
        return s

def load_proc_cfg( cm=None, cfg_dir=None, f=None, pcfg=None ):
    r = load_file( f, modules[__name__] ) if f else proc_cfg()
    r._cm = cm
    r._pcfg = pcfg
    r._cfg_dir = cfg_dir
    return r

