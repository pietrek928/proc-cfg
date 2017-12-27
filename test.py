#!/usr/bin/python

import stm
import gui

w = gui.Gtk.Window( title='aaaaaaaa' )
pc = stm.processor()

#p2 = stm.gpio_pin()
#p2.test_freq2 = 8e6
p = stm.gpio_pin()
p.n='p5'
p.num = 5
#p2.n='p2'
p.test_freq2 = 8e6
p.en = True
#p.p=p
#p.p2=p2
p.tiles = True
p.child_order = [  ]
p.tiles_edit = True
#p2.p3=p
#p2.tiles = True
#p2.tiles_edit = True
#p.n='p1'; #p2.n='p2'

gp = stm.gpio()
gp.en = True
gp.n = 'A'
gp.id = 'A'
gp.p = p

pc.n = 'procek_xd'
pc.gp = gp
pc.fix_parent()

#w = p.show_window() #"""
#w.connect("destroy",gui.Gtk.main_quit)
#w.show_all()

gp.child_order = ['p']
w = gp.show_window() #"""
w.connect("destroy",gui.Gtk.main_quit)
w.show_all()

gui.Gtk.main()

pc.gen_setup(decl=True)

"""
e = gui.Et.Element("root")
p.xml_store( e )
tree = gui.Et.ElementTree(e)
tree.write("a.xml") """


