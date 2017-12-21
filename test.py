#!/usr/bin/python

import stm
import gui

w = gui.Gtk.Window( title='aaaaaaaa' )
pc = stm.processor()

p2 = stm.gpio_pin()
p2.test_freq2 = 8e6
p = stm.gpio_pin()
p.n='p1'
p2.n='p2'
p.test_freq2 = 8e6
p.p=p
p.p2=p2
p.tiles = True
p.child_order = [ 'p', 'p2' ]
p.tiles_edit = True
p2.p3=p
p2.tiles = True
p2.tiles_edit = True
p.n='p1'; p2.n='p2'

gp = stm.gpio()
gp.n = 'A'
gp.p = p

pc.gp = gp
pc.gen_setup()

w.add( p.show(show_tiles=True) )#"""
#w.add(p.render_tree(sel_cb=print))
w.connect("destroy",gui.Gtk.main_quit)
w.show_all()

gui.Gtk.main()

"""
e = gui.Et.Element("root")
p.xml_store( e )
tree = gui.Et.ElementTree(e)
tree.write("a.xml") """


