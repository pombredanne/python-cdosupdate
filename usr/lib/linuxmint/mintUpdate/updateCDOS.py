#!/usr/bin/env python
# coding: utf-8
import gtk
import tempfile
import subprocess
import time
import threading
import gobject
import os
import commands
import itertools
from globalParameter import *
gtk.gdk.threads_init()

class ChooseVBox(gtk.VBox):
    def __init__(self, w, h, m):
        gtk.VBox.__init__(self)
        self.set_size_request(w, h)
        self.pack()
        self.main = m
        
    def celldatafunction_checkbox(self, column, cell, model, iter):
        cell.set_property("activatable", True)
        checked = model.get_value(iter, 0)
        if (checked == "true"):
            cell.set_property("active", True)
        else:
            cell.set_property("active", False)

    def toggled(self, renderer, path, treeview):
        model = treeview.get_model()
        iter = model.get_iter(path)
        if (iter != None):
            checked = model.get_value(iter, 0)
            if (checked == "true"):
                model.set_value(iter, 0, "false")
            else:
                model.set_value(iter, 0, "true")    

    def btn_accept_clicked(self, button, treeview):
        model = treeview.get_model()
        iter = model.get_iter_first()
        funcnames = []
        while (iter != None):
            checked = model.get_value(iter, 0)
            if (checked == "true"):
                funcnames.append(model.get_value(iter, 2))
            iter = model.iter_next(iter)
        #print "Your selection:", funcnames
        t = threading.Thread(target=self.main.redirect2process, args=(funcnames,))
        t.start()

    def btn_cancel_clicked(self, button):
        global model_data
        self.main.window.hide()
        #pid = os.getpid()    
        #os.system("kill -9 %s &" % pid)

    def pack(self):
        label = gtk.Label()
        label.set_markup("<b>" + _("The following customization will be exexuted:") + "</b>")
        label.set_alignment(0, 0.5)

        self.treeview_choose = gtk.TreeView()
        cr = gtk.CellRendererToggle()
        cr.connect("toggled", self.toggled, self.treeview_choose)
        column1 = gtk.TreeViewColumn(_("Check"), cr)
        column1.set_cell_data_func(cr, self.celldatafunction_checkbox)
        column2 = gtk.TreeViewColumn(_("Description"), gtk.CellRendererText(), text=1)
        #column2.set_resizable(True)
        column3 = gtk.TreeViewColumn(_("Command"), gtk.CellRendererText(), text=2)
        #column3.set_resizable(True)
        self.treeview_choose.append_column(column1)
        self.treeview_choose.append_column(column2)
        self.treeview_choose.append_column(column3)
        model = gtk.TreeStore(str, str, str)
        self.treeview_choose.set_model(model)
        self.treeview_choose.set_headers_clickable(False)
        self.treeview_choose.set_reorderable(False)

        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_shadow_type(gtk.SHADOW_IN)
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.add(self.treeview_choose)

        hbuttonbox = gtk.HButtonBox()
        hbuttonbox.set_spacing(50)
        hbuttonbox.set_layout(gtk.BUTTONBOX_CENTER)
        btn_accept = gtk.Button(_("accept"))
        btn_accept.connect("clicked", self.btn_accept_clicked, self.treeview_choose)
        btn_cancel = gtk.Button(_("cancel"))
        btn_cancel.connect("clicked", self.btn_cancel_clicked)
        hbuttonbox.pack_start(btn_accept)
        hbuttonbox.pack_end(btn_cancel)

        self.pack_start(label, False, False, 10)
        self.pack_start(scrolledWindow, True, True, 0)
        self.pack_start(hbuttonbox, False, False, 5)
    def refresh_treeview(self):
        global model_data
        model = self.treeview_choose.get_model()
        for data in model_data:
            iter = model.insert_before(None, None)
            model.set_value(iter, 0, data[0])
            model.set_value(iter, 1, data[1])
            model.set_value(iter, 2, data[2])
            #' '.join(str(elem) for elem in data[2])
            #print data


class ProcessVBox(gtk.VBox):
    def __init__(self, w, h, m):
        gtk.VBox.__init__(self)
        self.text = 0
        self.main = m
        self.set_size_request(w, h)
        self.textview = gtk.TextView()
        self.textbuf = gtk.TextBuffer()
        self.textview.set_buffer(self.textbuf)
        self.hbuttonbox = gtk.HButtonBox()
        self.pack()
    def refresh_textbuf(self, allcommands):
        for cmd in allcommands:
            #print cmd.split(' ')
            popen = subprocess.Popen(cmd.split(' '), stdout = subprocess.PIPE)
            out, error = popen.communicate()
            if(out == None):
                out = ""
            if(error == None):
                error = ""
            gtk.gdk.threads_enter()
            self.textbuf.insert_at_cursor(out)
            self.textbuf.insert_at_cursor(error)
            end_mark = self.textbuf.get_insert()
            self.textview.scroll_to_mark(end_mark, 0.0)
            gtk.gdk.threads_leave()
        self.hbuttonbox.set_sensitive(True)

    def btn_accept_clicked(self, button):
        #print button.get_label()
        t = threading.Thread(target=self.refresh_textbuf)
        t.start()     
    def btn_close_clicked(self, button):
        #print button.get_label()
        self.main.window.hide()
        #pid = os.getpid()    
        #os.system("kill -9 %s &" % pid)
    def pack(self):
        label = gtk.Label()
        label.set_markup("<b>" + _("Status output:") + "</b>")
        label.set_alignment(0, 0.5)
        scrolledWindow = gtk.ScrolledWindow()
        scrolledWindow.set_shadow_type(gtk.SHADOW_IN)
        scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledWindow.add(self.textview)

        self.hbuttonbox.set_spacing(50)
        self.hbuttonbox.set_layout(gtk.BUTTONBOX_CENTER)
        #btn_accept = gtk.Button("accept")
        #btn_accept.connect("clicked", self.btn_accept_clicked)
        btn_close = gtk.Button(_("close"))
        btn_close.connect("clicked", self.btn_close_clicked)
        self.hbuttonbox.pack_start(btn_close)
        #hbuttonbox.pack_end(btn_cancel)

        self.pack_start(label, False, False, 10)
        self.pack_start(scrolledWindow, True, True, 0)
        self.pack_start(self.hbuttonbox, False, False, 5)
        self.hbuttonbox.set_sensitive(False)

    def start_process(self, funcnames):
        t = threading.Thread(target=self.refresh_textbuf, args=(funcnames,))
        t.start()   
        #print "in start process."  

class MainWindow():
    def __init__(self):
        self.width = 600
        self.height = 400
        self.choose_x = 0
        self.process_x = self.width
        self.fix = gtk.Fixed()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(_("System Customization"))
        self.window.set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
        self.window.set_default_size(self.width, self.height)
        self.window.set_geometry_hints(self.window, self.width, self.height, self.width, self.height)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.vbox_choose = ChooseVBox(self.width, self.height, self)
        #self.vbox_choose.set_main(self)
        self.vbox_process = ProcessVBox(self.width, self.height, self)

    def redirect2process(self, funcnames):
        step = 200
        while(self.process_x > 0):
            self.choose_x = self.choose_x - step
            self.process_x = self.process_x - step
            gtk.gdk.threads_enter()
            self.fix.move(self.vbox_choose, self.choose_x, 0)
            self.fix.move(self.vbox_process, self.process_x, 0)
            gtk.gdk.threads_leave()
            time.sleep(0.1)
            #print choose_x, process_x
        if(self.process_x < 0):
            self.choose_x = -1 * self.width
            self.process_x = 0
            gtk.gdk.threads_enter()
            self.fix.move(self.vbox_choose, self.choose_x, 0)
            self.fix.move(self.vbox_process, self.process_x, 0)
            gtk.gdk.threads_leave()
        self.vbox_process.start_process(funcnames)
            
    def openWindow(self):
        self.fix.put(self.vbox_choose, self.choose_x, 0)
        self.fix.put(self.vbox_process, self.process_x, 0)
        self.fix.show()
        self.vbox_choose.refresh_treeview()
        self.window.add(self.fix)
        self.window.show_all()
        gtk.main()

global model_data
model_data = []

def test():
    global model_data
    name = 'ghostscript'
    model_data.append(('true', _("Update Package") + name, 'apt-get -y --force-yes install ' + name))
    cmdstatus, cmdoutput = commands.getstatusoutput('cdos-upgrade --check')
    if(cmdstatus == 0):
        if(cmdoutput != ''):
            funcnames, funcdescs = cmdoutput.split('\n')
            descs = funcdescs.split('####')
            cmds = funcnames.split('####')
            for descs,cmd in itertools.izip(descs, cmds):
                model_data.append(('true', descs, cmd))
    else:
        error_dialog(_("Command fail: cdos-upgrade --check"))
    model_data = []
    if(len(model_data) > 0):
        main = MainWindow()
        main.openWindow()
    else:
        warning_dialog(_("All customization has achieved."))

def update_cdos(widget, treeView, statusIcon, wTree):
    global model_data
    model_data = []

    cmdstatus, cmdoutput = commands.getstatusoutput('apt-get install cdos-upgrade')
    if(cmdstatus != 0):
        error_dialog(_("Package cdos-upgrade is not install correct."))
        return False

    model = treeView.get_model()
    iter = model.get_iter_first()
    num_selected = 0
    while (iter != None):
        name = model.get_value(iter, model_name)
        #print pkginfodict[name].origin
        if(pkginfodict[name].label == "CDOS"):
            model.set_value(iter, 0, "true")
            num_selected = num_selected + 1
            model_data.append(('true', 'Update Package' + name, 'apt-get -y --force-yes install ' + name))
        else:
            model.set_value(iter, 0, "false")
        iter = model.iter_next(iter)
    cmdstatus, cmdoutput = commands.getstatusoutput('cdos-upgrade --check')
    if(cmdstatus == 0):
        if(cmdoutput != ''):
            funcnames, funcdescs = cmdoutput.split('\n')
            descs = funcdescs.split('####')
            cmds = funcnames.split('####')
            for descs,cmd in itertools.izip(descs, cmds):
                model_data.append(('true', descs, cmd))
    else:
        error_dialog(_("Command fail: cdos-upgrade --check"))
        return False
    if(len(model_data) > 0):
        main = MainWindow()
        main.openWindow()
    else:
        warning_dialog(_("All customization has achieved."))
        return False


#    for row in model:
#        if(pkginfodict[row[1]].origin == "cosdesktop"):
#            row[0] = "true"

#    if(num_selected > 0):
#        cmd = ["sudo", "/usr/sbin/synaptic", "--hide-main-window",  \
#                "--non-interactive", "--parent-window-id", "%s" % self.wTree.get_widget("window1").window.xid]
#        cmd.append("-o")
#        cmd.append("Synaptic::closeZvt=true")
#        cmd.append("--progress-str")
#        cmd.append("\"" + _("Please wait, this can take some time") + "\"")
#        cmd.append("--finish-str")
#        cmd.append("\"" + _("Update is complete") + "\"")
#        f = tempfile.NamedTemporaryFile()
#        for pkg in pkgsname:
#            f.write("%s\tinstall\n" % pkg)
#        cmd.append("--set-selections-file")
#        cmd.append("%s" % f.name)
#        f.flush()
#        comnd = Popen(' '.join(cmd), stdout=log, stderr=log, shell=True)
#        returnCode = comnd.wait()
#hbuttonbox.set_sensitive(False)
