#!/usr/bin/bash

import xml.etree.ElementTree as Et;
from sys import modules

from gui import xml_storable, _store_obj

def dict_get_sorted( d, ll ):
    tt = []
    for vn,v in d.items():
        tt.append( v )
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
        if ( hasattr( s, 'e' ) ): e.attrib[ 'e' ] = str( s.e )
    def xml_load( s, e, cm ):
        s.n = e.attrib[ 'n' ]
        s.b = int( e.attrib['b'] )
        ee = e.attrib.get('e')
        if ( ee ):
            s.e=int(ee)

class struct_field( xml_storable ):
    def __init__( s ):
        s.b = {}
    def make_array( s, n=1 ):
        if hasattr(s,'ne'): return
        s.le = s.l
        s.ne = n
        s.l = s.le * s.ne
    def join( s, f ):
        s.make_array()
        f.make_array()
        if not s.le == f.le: ValueError('different element sizes')
        off = s.l*8
        for nn,i in f.b.items():
            i.b += off
            if hasattr( i, 'e' ): i.b += off
            s.b[ nn ] = i
        s.ne += f.ne
        s.l = s.le*s.ne
        del f
    def xml_store( s, e ):
        e.attrib[ 'n' ] = s.n
        if ( hasattr( s, 'ne' ) ):
            e.attrib[ 'ne' ] = str( s.ne )
            e.attrib[ 'le' ] = str( s.le )
        else:
            e.attrib[ 'l' ] = str( s.l )
        if hasattr( s, 't' ):
            e.attrib[ 't' ] = s.t
        if hasattr( s, 'doc' ):
            e.attrib[ 'doc' ] = s.doc
        ee = Et.SubElement( e, 'v' )
        _store_obj( ee, dict_get_sorted( s.b, lambda v: v.b ) )
    def get_descr( s ):
        try:
            return '{}({})'.format( s.n, s.doc )
        except AttributeError:
            return s.n

class struct_descr( xml_storable ):
    def __init__( s ):
        s.l = 0
        s.t = {}
        s.tt = []
    def add( s, f ):
        f.off = s.l
        s.l += f.l
        s.t[f.n] = f
    def union_fields( s, tp ): # called once for single object
        un = None
        for i in s.tt:
            if un == None:
                for j in tp:
                    if i.n.startswith( j[0] ) and i.n.endswith( j[1] ):
                        un = i
                        s.t.pop( i.n )
                        lj = j
                        i.n = j[0]+j[1]
                        s.add( i )
                        break;
            else:
                if ( i.n.startswith( lj[0] ) and i.n.endswith( lj[1] ) ) or hasattr(i,'reserved'):
                    s.t.pop( i.n )
                    un.join( i )
                else: un = None
        delattr( s, 'tt' )
    def clr( s ):
        if hasattr( s, 'tt' ): delattr( s, 'tt' )

class periph_obj( xml_storable ):
    def gen_setup( s, out, fn, fl, mode ): # TODO: faster version in C++
        f = s.t.t[ fn ]
        out.putl('   /* {}: {}  */'.format(f.get_descr(),fl))
        zu = mode.zu # zero used
        zz = mode.zz # zero all
        if zz: zu=False
        f.make_array() # !!!!!!
        vv = [0]*f.ne
        nbits = f.le*8
        just_ones = (1<<nbits)-1
        if zu:
            uu = [just_ones]*f.ne
        for n,v in fl.items():
            ff = f.b[ n ]
            nn = ff.b//nbits
            ss = ff.b %nbits
            vv[nn] |= int(v)<<ss # TODO: unconstant value
            if zu and not mode.ww:
                uu[nn] &= ~(((1<<(1 if not hasattr(ff,'e') else ((ff.e%nbits)-ss+1)))-1)<<ss);
        fpos = s.a+f.off;
        pp =( '=' if zz or mode.ww else '|=' ) # preserve previous
        vol = ( 'volatile ' if mode.vol else '' )
        for it in range(len(vv)): # TODO: preserve current vals
            fp = '( *({}uint{}_t*){})'.format(vol, f.le*8, hex(fpos+it*f.le))
            nv = None
            av = None
            if zz or vv[it]!=0:
                nv = '0x%0*x' % (nbits//4,vv[it])
            if zu and uu[it]!=just_ones:
                av = '0x%0*x' % (nbits//4,uu[it])
            if av and nv:
                out.putl('{0}=((({0})&{1})|{2});'.format(fp, av, nv))
            elif nv:
                out.putl(fp+pp+nv+';')
            elif av:
                out.putl('{}&={};'.format(fp, av)) # TODO: negate flag
    def __init__( s ):
        a=0

class proc_cfg( xml_storable):
    def __init__( s, cm=None, cfg_dir=None, f=None, pcfg=None ):
        s.clear_data()
        s._cm = cm
        s._pcfg = pcfg
        s._cfg_dir = cfg_dir
        if f:
            s.load_file( f, modules[ __name__ ] )
    def clear_data( s ):
        s.periph_data = {}
        s.types = {}
        s.vars = {}
    def import_cfg( s, n ):
        try:
            r = s.load_obj( '{}/{}.xml'.format( s._cfg_dir, n ), s._cm )
            r.cfg_name = n;
            return r
        except KeyError:
            return s._pcfg.import_cfg( n )
    def get_periph( s, n ): # TODO: cache
        try:
            return s.periph[ n ]
        except KeyError:
            return s._pcfg.get_periph( n )
    def get_var( s, n ): # TODO: cache
        try:
            return s.vars[n]
        except KeyError:
            return s._pcfg.get_var( n )

