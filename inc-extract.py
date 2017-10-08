#!/usr/bin/python

import sys;
import re;
import bisect;

import periph_class as pc

end_chr = ( '/', '\n' )
delim_chr = ( ';', ',' )
typedef_known_words = ( '__IO', '__I', '{' )
define_bad_begin = [
        'IS_',
        'RCC_CFGR_PLLMULL_',
        'RCC_CFGR_PLLMULL0',
        'RCC_CFGR_PLLMULL1',
        'RCC_CFGR_PLLMULL2',
        'RCC_CFGR_PLLMULL3',
        'RCC_CFGR_PLLMULL4',
        'RCC_CFGR_PLLMULL5',
        'RCC_CFGR_PLLMULL6',
        'RCC_CFGR_PLLMULL7',
        'RCC_CFGR_PLLMULL8',
        'RCC_CFGR_PLLMULL9',
        ]
define_bad_begin.sort()
define_pref_swap = [
        ('DMA_Sx','DMA_Stream_'),
        ]
define_pref_swap.sort( key=lambda a:a[0] )

type_len = {
        'uint8_t':1,
        'uint16_t':2,
        'uint32_t':4,
        }
processor = pc.proc_cfg()
periph_data = processor.periph_data
n_obj_set = processor.types

rn_obj_set = {}

def str_match_begin( A, w ):
    try:
        a = A[ bisect.bisect_right( A, w )-1 ]
        if w.startswith( a ): return True
    except:
        return False
    return False

class proc_typedef:
    def __init__( s ):
        s.start = True
        s.o = pc.struct_descr()
        s.f = None

    def proc( s, w ):
        if hasattr( s, 'start' ):
            if not (w == 'struct'): return False
            delattr( s, 'start' )
            return True
        if hasattr( s, 'stop' ): s.rn=w; return False
        if w[0] == '}':
            if len(w)>3: s.rn = w[1:]; return False
            else:
                s.stop = True
                return True
        if s.f == None:
            if not type_len.get(w) == None:
                s.f = pc.struct_field()
                s.f.l = type_len.get(w)
            else:
                if rn_obj_set.get(w) != None:
                    s.f = pc.struct_field()
                    o = rn_obj_set.get(w)
                    s.f.l = o.l
                    s.f.t = o.n
                else:
                    if not w in typedef_known_words:
                        print( 'WARNING: unknown type '+w )
        else:
            if w.endswith(']'): # array
                w = w[:-1]
                ( w, l ) = w.split( '[' )
                if l.startswith('0x'): l=int(l,16)
                else: l=int(l)
                s.f.make_array( l )
            s.f.n = w # TODO: reserved, array, multireg
            if s.f.n.startswith( 'Reserved' ) or s.f.n.startswith( 'RESERVED' ):
                s.f.reserved = True
            #print(w)
            s.o.add( s.f )
            s.o.tt.append( s.f )
            s.prev_o = s.f
            s.f = None
        return True

    def proc_doc( s, doc ):
        if hasattr( s, 'prev_o' ):
            while doc and doc[0] in ' /*!<':
                doc = doc[1:]
            while doc and doc[-1] in ' /*!<':
                doc = doc[:-1]
            doc = doc.split('  ')
            d = ' '.join([ i for i in doc if len(i)>3])
            s.prev_o.doc = d

    def __del__( s ):
        if hasattr( s, 'start' ): return;
        if not hasattr( s, 'rn' ): print( 'struct interpreting error; line: '+str(s.ln) ); return
        s.n = s.rn
        if s.n.endswith('TypeDef'): s.n=s.n[:-len('TypeDef')]
        if s.n.endswith('_'): s.n=s.n[:-1]
        s.o.n=s.n; s.o.rn=s.rn;
        n_obj_set[s.o.n] = s.o
        rn_obj_set[s.o.rn] = s.o
        #print( 'end typedef ' + s.n + '; size: '+str(s.o.l) )

reg_pos_data = {}
addr_data = {}

class proc_define:
    def __init__( s ):
        s.v = ''
    def proc( s, w ):
        if not hasattr( s, 'n' ):
            s.n = w
            return True
        s.v += w
        return True
    def proc_doc( s, doc ):
        if hasattr( s, 'prev_o' ):
            s.prev_o.doc = doc
    def __del__( s ):
        if not hasattr( s, 'n' ):
            print( 'define interpreting error; line: '+str(s.ln) )
            return;
        try:
            bs = define_pref_swap[ bisect.bisect_right( define_pref_swap, (s.n,'') )-1 ]
            if s.n.startswith( bs[0] ):
                s.n = bs[1] + s.n[len(bs[0]):]
        except:
            fooooooooooooo=0
        if str_match_begin( define_bad_begin, s.n ):
            print( 'define has forbidden begin', s.n )
            return;
        if s.n.endswith('_BASE'):
            nn = s.n[:-len('_BASE')]
            vv = re.split( '\)|\(|\+', s.v )
            while len(vv[0])==0: vv=vv[1:]
            while len(vv[-1])==0: vv=vv[:-1]
            bv = None
            av = 0
            if vv[0].endswith('_BASE'): bv=vv[0][:-len('_BASE')]
            if vv[-1].startswith('0x'): av=int(vv[-1],16)
            if not bv == None: av += addr_data[bv]
            addr_data[nn] = av
            #print( 'periph: ', nn, 'addr: ', av )
            return;
        if s.v.endswith('_BASE)'):
            vv = re.split( '\)|\(|\*', s.v )
            while len(vv[0])==0: vv=vv[1:]
            while len(vv[-1])==0: vv=vv[:-1]
            if vv[-1].endswith('_BASE'):
                o = pc.periph_obj();
                o.n = s.n
                o.t = rn_obj_set[vv[0]]
                o.a = addr_data[vv[-1][:-len('_BASE')]]
                #print( 'periph: ', s.n, format( addr_data[vv[-1][:-len('_BASE')]], '08x') )
                periph_data[s.n] = o
            return;
        nn = s.n.split('_')
        if True: #not nn[0] in define_bad_begin:
            o = None
            nnl=0;
            if nn[-1] == 'Pos':
                pn = '_'.join(nn[0:-1])
                reg_pos_data[ pn ] = int(s.v[1:-2])
                return;
            if nn[-1] == 'Msk':
                pn = '_'.join(nn[0:-1])
                s.pp = reg_pos_data.get(pn)
                if s.pp == None: return;
                nn=nn[0:-1]
            oname = nn[0]; nn=nn[1:]
            for i in nn:
                if not n_obj_set.get(oname) == None:
                    nl = nnl
                    o = n_obj_set.get(oname)
                oname += '_'+i
                nnl=nnl+1
            if not o == None:
                nn = nn[nl:]
                if len(nn)==2 and '(' in s.v:
                    rn=nn[0]
                    bn = nn[1]
                    r=o.t.get( rn )
                    if not r == None:
                        msk = None
                        if hasattr( s, 'pp' ):
                            try:
                                vv = s.v.split('<')
                                msk = int(vv[0][1:-1],16)<<s.pp
                            except:
                                print('processing define error '+s.n+' '+s.v)
                        else:
                            try:
                                vv = s.v.split(')')
                                if len(vv[-1])<1: vv=vv[0:-1]
                                vv=vv[-1]
                                if vv.startswith('('): vv=vv[1:]
                                if vv.endswith('U'): vv=vv[0:-1]
                                msk = int(vv,16)
                            except:
                                print('processing define error '+s.n+' '+s.v)
                        if msk == None: return
                        bb = r.b[bn] = pc.reg_bit()
                        bb.set( bn, msk )
                        s.prev_o = bb
                        #print( 'reg '+rn+'('+bn+'): '+str(bb.b)+'-'+str(bb.b if not hasattr(bb,'e') else bb.e)+'    '+bb.doc )
        #print( 'end define '+s.n+' '+s.v )

proc_obj_tab = {
        'typedef':proc_typedef,
        '#define':proc_define,
        }

#"""
proc_obj = None
#print(proc_obj_tab)
n = 0
with open( sys.argv[1] ) as f:
    l = ' '
    while l:
        if len(l) > 1:
            l = re.split(' |;|\n',l)
            ii=0
            for w in l:
                ii=ii+1
                if len(w)<1: continue;
                if w[-1] in delim_chr: w=w[:-1]
                if w[0] in end_chr : break;
                if proc_obj == None:
                    aa = proc_obj_tab.get( w )
                    if aa != None:
                        proc_obj = aa()
                        proc_obj.ln = n
                else:
                    if not proc_obj.proc( w ):
                        proc_obj = None
        if hasattr( proc_obj, 'proc_doc' ):
            proc_obj.proc_doc( ' '.join(l[ii-1:]) )
        if isinstance( proc_obj, proc_define ): proc_obj=None
        l = ' '
        n = n+1
        try:
            l = f.readline()
        except:
            print( 'reading line error; line: '+str(n) )

n_obj_set[ 'RCC' ].union_fields( [ [ '', 'ENR' ] ] )

processor.store_file( 'a.xml', n='proc' )

from sys import modules
tst = pc.proc_cfg()
tst.load_file( 'a.xml', pc )

import processor as pp
oo = pp.out_proc()
mm = pp.mode_obj()
mm.vol = True
#mm.zz = True
mm.zu = True
periph_data[ 'RCC' ].gen_setup( oo, 'ENR', {'ADC1EN':1}, mm ) #"""

"""
pp = Et.Element('processor')
pdata = Et.SubElement( pp, 'periph_data' )
for vn,v in periph_data.items():
    v.xml_store( pdata );
pdescr = Et.SubElement( pp, 'typesr' )
for vn,v in n_obj_set.items():
    v.xml_store( pdescr );
Et.ElementTree( pp ).write( 'a.xml' );
#"""

"""
top = Et.Element('top')

comment = Et.Comment('Generated for PyMOTW')
top.append(comment)

child = Et.SubElement(top, 'child')
child.text = 'This child contains text.'

child_with_tail = Et.SubElement(top, 'child_with_tail')
child_with_tail.text = 'This child has regular text.'
child_with_tail.tail = 'And "tail" text.'
child_with_tail.attrib['ttaagg'] = "tag"
print( child_with_tail.attrib['ttaagg'] )

child_with_entity_ref = Et.SubElement(top, 'child_with_entity_ref')
child_with_entity_ref.text = 'This & that'

Et.ElementTree( top ).write( 'a.xml' ); #"""

