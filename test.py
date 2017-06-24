#!/usr/bin/python

import stm
import gui

w = gui.Gtk.Window( title='aaaaaaaa' )
p2 = stm.gpio_pin()
p2.test_freq2 = 8e6
p = stm.gpio_pin()
p.test_freq2 = 8e6
p.p2=p2
p.tiles = True
p.n='p1'; p2.n='p2'
w.add( p.show() )
w.connect("destroy",gui.Gtk.main_quit)
w.show_all()

gui.Gtk.main()

e = gui.Et.Element("root")
p.xml_store( e )
tree = gui.Et.ElementTree(e)
tree.write("a.xml")


