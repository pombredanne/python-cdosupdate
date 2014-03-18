#!/usr/bin/env python
import gtk
import pygtk

CDOS_LABEL = "CDOS"
model_check = 0
model_name = 1
model_levelpix = 2
model_oldversion = 3
model_newversion = 4
model_size = 5
model_strsize = 6
model_strlevel = 7
model_des = 8
model_warning = 9
model_extrainfo = 10
pkginfodict={}

def error_dialog(message):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, None)
    dialog.set_title(_("ERROR"))
    dialog.set_markup("<b>" + message + "</b>")
    label = gtk.Label(_("Contact us: cdos_support@iscas.ac.cn"))
    dialog.vbox.pack_start(label)
    dialog.set_default_size(400, 300)
    dialog.show_all()
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.run()
    dialog.destroy()
    return False

def warning_dialog(message):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, None)
    dialog.set_title(_("WARNING"))
    dialog.set_markup("<b>" + message + "</b>")
    dialog.set_default_size(400, 300)
    dialog.show_all()
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.run()
    dialog.destroy()
    return False
