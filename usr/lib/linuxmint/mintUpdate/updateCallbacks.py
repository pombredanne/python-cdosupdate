#!/usr/bin/env python
# coding: utf-8
import gtk
import subprocess
import time
import threading
import os
import commands
import itertools
import fnmatch
from configobj import ConfigObj
import globalParameter as g
from updateClasses import RefreshThread
from updateClasses import InstallThread
from updateClasses import ChangelogRetriever

gtk.gdk.threads_init()

        
def add_to_ignore_list(widget, treeview_update, pkg, statusIcon, wTree):
    os.system("echo \"%s\" >> /etc/linuxmint/mintupdate.ignored" % pkg)
    #force_refresh(widget, treeview_update, statusIcon, wTree)
    t = threading.Thread(target=refresh_status, args=(treeview_update, statusIcon, wTree, [pkg]))
    t.start()

def show_pkg_info(widget, selected_package, statusIcon, wTree):
    return False

def menuPopup(widget, event, treeview_update, statusIcon, wTree):
    if event.button == 3:
        (model, iter) = widget.get_selection().get_selected()
        if (iter != None):
            selected_package = model.get_value(iter, g.model_name)
            menu = gtk.Menu()
            ignorePkg = gtk.MenuItem(_("Ignore updates for this package"))
            ignorePkg.connect("activate", add_to_ignore_list, treeview_update, selected_package, statusIcon, wTree)
            showInfo = gtk.MenuItem(_("Show package info"))
            showInfo.connect("activate", show_pkg_info, selected_package, statusIcon, wTree)
            menu.append(ignorePkg)
            menu.append(showInfo)        
            menu.show_all()        
            menu.popup(None, None, None, 3, 0)

def size_to_string(size):
    strSize = str(size) + _("B")
    if (size >= 1024):
        strSize = str(size / 1024) + _("KB")
    if (size >= (1024 * 1024)):
        strSize = str(size / (1024 * 1024)) + _("MB")
    if (size >= (1024 * 1024 * 1024)):
        strSize = str(size / (1024 * 1024 * 1024)) + _("GB")
    return strSize
def read_configuration():
    config = ConfigObj("/etc/linuxmint/mintUpdate.conf")
    prefs = {}
    #Read refresh config
    try:
        prefs["timer_minutes"] = int(config['refresh']['timer_minutes'])
        prefs["timer_hours"] = int(config['refresh']['timer_hours'])
        prefs["timer_days"] = int(config['refresh']['timer_days'])
    except:
        prefs["timer_minutes"] = 15
        prefs["timer_hours"] = 0
        prefs["timer_days"] = 0
    #Read update config
    try:
        prefs["delay"] = int(config['update']['delay'])
        prefs["ping_domain"] = config['update']['ping_domain']
        prefs["dist_upgrade"] = (config['update']['dist_upgrade'] == "True")
    except:
        prefs["delay"] = 30
        prefs["ping_domain"] = "google.com"
        prefs["dist_upgrade"] = True
    #Read icons config
    try:
        g.icon_busy = config['icons']['busy']
        g.icon_up2date = config['icons']['up2date']
        g.icon_updates = config['icons']['updates']
        g.icon_error = config['icons']['error']
        g.icon_unknown = config['icons']['unknown']
        g.icon_apply = config['icons']['apply']
    except:
        g.icon_busy = "/usr/lib/linuxmint/mintUpdate/icons/base.svg"
        g.icon_up2date = "/usr/lib/linuxmint/mintUpdate/icons/base-apply.svg"
        g.icon_updates = "/usr/lib/linuxmint/mintUpdate/icons/base-info.svg"
        g.icon_error = "/usr/lib/linuxmint/mintUpdate/icons/base-error2.svg"
        g.icon_unknown = "/usr/lib/linuxmint/mintUpdate/icons/base.svg"
        g.icon_apply = "/usr/lib/linuxmint/mintUpdate/icons/base-exec.svg"
    #Read levels config
    try:
        prefs["level1_visible"] = (config['levels']['level1_visible'] == "True")
        prefs["level2_visible"] = (config['levels']['level2_visible'] == "True")
        prefs["level3_visible"] = (config['levels']['level3_visible'] == "True")
        prefs["level4_visible"] = (config['levels']['level4_visible'] == "True")
        prefs["level5_visible"] = (config['levels']['level5_visible'] == "True")
        prefs["level1_safe"] = (config['levels']['level1_safe'] == "True")
        prefs["level2_safe"] = (config['levels']['level2_safe'] == "True")
        prefs["level3_safe"] = (config['levels']['level3_safe'] == "True")
        prefs["level4_safe"] = (config['levels']['level4_safe'] == "True")
        prefs["level5_safe"] = (config['levels']['level5_safe'] == "True")
    except:
        prefs["level1_visible"] = True
        prefs["level2_visible"] = True
        prefs["level3_visible"] = True
        prefs["level4_visible"] = False
        prefs["level5_visible"] = False
        prefs["level1_safe"] = True
        prefs["level2_safe"] = True
        prefs["level3_safe"] = True
        prefs["level4_safe"] = False
        prefs["level5_safe"] = False
    #Read columns config
    try:
        prefs["level_column_visible"] = (config['visible_columns']['level'] == "True")
    except:
        prefs["level_column_visible"] = True
    try:
        prefs["package_column_visible"] = (config['visible_columns']['package'] == "True")
    except:
        prefs["package_column_visible"] = True
    try:
        prefs["old_version_column_visible"] = (config['visible_columns']['old_version'] == "True")
    except:
        prefs["old_version_column_visible"] = True
    try:
        prefs["new_version_column_visible"] = (config['visible_columns']['new_version'] == "True")
    except:
        prefs["new_version_column_visible"] = True
    try:
        prefs["size_column_visible"] = (config['visible_columns']['size'] == "True")
    except:
        prefs["size_column_visible"] = True
    #Read window dimensions
    try:
        prefs["dimensions_x"] = int(config['dimensions']['x'])
        prefs["dimensions_y"] = int(config['dimensions']['y'])
        prefs["dimensions_pane_position"] = int(config['dimensions']['pane_position'])
    except:
        prefs["dimensions_x"] = 790
        prefs["dimensions_y"] = 540
        prefs["dimensions_pane_position"] = 230
    #Read package blacklist
    try:
        prefs["blacklisted_packages"] = config['blacklisted_packages']
    except:
        prefs["blacklisted_packages"] = []
    return prefs

# statusicon-setting
def force_refresh(widget, treeview, statusIcon, wTree):
    refresh = RefreshThread(treeview, statusIcon, wTree)
    refresh.start()
def open_information(widget):
    gladefile = "/usr/lib/linuxmint/mintUpdate/mintUpdate.glade"
    prefs_tree = gtk.glade.XML(gladefile, "window3")
    prefs_tree.get_widget("window3").set_title(_("Information") + " - " + _("Update Manager"))
    prefs_tree.get_widget("window3").set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
    prefs_tree.get_widget("close_button").connect("clicked", info_cancel, prefs_tree)
    prefs_tree.get_widget("label1").set_text(_("Information"))
    prefs_tree.get_widget("label2").set_text(_("Log file"))
    prefs_tree.get_widget("label3").set_text(_("Permissions:"))
    prefs_tree.get_widget("label4").set_text(_("Process ID:"))
    prefs_tree.get_widget("label5").set_text(_("Log file:"))

    prefs_tree.get_widget("mode_label").set_text(str(g.MODE))
    prefs_tree.get_widget("processid_label").set_text(str(g.PID))
    prefs_tree.get_widget("log_filename").set_text(str(g.LOGFILE))
    txtbuffer = gtk.TextBuffer()
    txtbuffer.set_text(commands.getoutput("cat " + g.LOGFILE))
    prefs_tree.get_widget("log_textview").set_buffer(txtbuffer)

def open_preferences(widget, treeview, statusIcon, wTree):

    gladefile = "/usr/lib/linuxmint/mintUpdate/mintUpdate.glade"
    prefs_tree = gtk.glade.XML(gladefile, "window2")
    prefs_tree.get_widget("window2").set_title(_("Preferences") + " - " + _("Update Manager"))

    prefs_tree.get_widget("label37").set_text(_("Levels"))
    prefs_tree.get_widget("label36").set_text(_("Auto-Refresh"))
    prefs_tree.get_widget("label39").set_markup("<b>" + _("Level") + "</b>")
    prefs_tree.get_widget("label40").set_markup("<b>" + _("Description") + "</b>")
    prefs_tree.get_widget("label48").set_markup("<b>" + _("Tested?") + "</b>")
    prefs_tree.get_widget("label54").set_markup("<b>" + _("Origin") + "</b>")
    prefs_tree.get_widget("label41").set_markup("<b>" + _("Safe?") + "</b>")
    prefs_tree.get_widget("label42").set_markup("<b>" + _("Visible?") + "</b>")
    prefs_tree.get_widget("label43").set_text(_("Certified packages. Tested through Romeo or directly maintained by Linux Mint."))
    prefs_tree.get_widget("label44").set_text(_("Recommended packages. Tested and approved by Linux Mint."))
    prefs_tree.get_widget("label45").set_text(_("Safe packages. Not tested but believed to be safe."))
    prefs_tree.get_widget("label46").set_text(_("Unsafe packages. Could potentially affect the stability of the system."))
    prefs_tree.get_widget("label47").set_text(_("Dangerous packages. Known to affect the stability of the systems depending on certain specs or hardware."))
    prefs_tree.get_widget("label55").set_text(_("Linux Mint"))
    prefs_tree.get_widget("label56").set_text(_("Upstream"))
    prefs_tree.get_widget("label57").set_text(_("Upstream"))
    prefs_tree.get_widget("label58").set_text(_("Upstream"))
    prefs_tree.get_widget("label59").set_text(_("Upstream"))
    prefs_tree.get_widget("label81").set_text(_("Refresh the list of updates every:"))
    prefs_tree.get_widget("label82").set_text("<i>" + _("Note: The list only gets refreshed while the update manager window is closed (system tray mode).") + "</i>")
    prefs_tree.get_widget("label82").set_use_markup(True)
    prefs_tree.get_widget("label83").set_text(_("Update Method"))        
    prefs_tree.get_widget("label85").set_text(_("Icons"))
    prefs_tree.get_widget("label86").set_markup("<b>" + _("Icon") + "</b>")
    prefs_tree.get_widget("label87").set_markup("<b>" + _("Status") + "</b>")
    prefs_tree.get_widget("label95").set_markup("<b>" + _("New Icon") + "</b>")
    prefs_tree.get_widget("label88").set_text(_("Busy"))
    prefs_tree.get_widget("label89").set_text(_("System up-to-date"))
    prefs_tree.get_widget("label90").set_text(_("Updates available"))
    prefs_tree.get_widget("label99").set_text(_("Error"))
    prefs_tree.get_widget("label2").set_text(_("Unknown state"))
    prefs_tree.get_widget("label3").set_text(_("Applying updates"))
    prefs_tree.get_widget("label6").set_text(_("Startup delay (in seconds):"))
    prefs_tree.get_widget("label7").set_text(_("Internet check (domain name or IP address):"))
    prefs_tree.get_widget("label1").set_text(_("Ignored packages"))

    prefs_tree.get_widget("checkbutton_dist_upgrade").set_label(_("Include updates which require the installation or the removal of other packages"))

    prefs_tree.get_widget("window2").set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
    prefs_tree.get_widget("window2").show()
    prefs_tree.get_widget("pref_button_cancel").connect("clicked", pref_cancel, prefs_tree)
    prefs_tree.get_widget("pref_button_apply").connect("clicked", pref_apply, prefs_tree, treeview, statusIcon, wTree)

    prefs_tree.get_widget("button_icon_busy").connect("clicked", change_icon, "busy", prefs_tree, treeview, statusIcon, wTree)
    prefs_tree.get_widget("button_icon_up2date").connect("clicked", change_icon, "up2date", prefs_tree, treeview, statusIcon, wTree)
    prefs_tree.get_widget("button_icon_updates").connect("clicked", change_icon, "updates", prefs_tree, treeview, statusIcon, wTree)
    prefs_tree.get_widget("button_icon_error").connect("clicked", change_icon, "error", prefs_tree, treeview, statusIcon, wTree)
    prefs_tree.get_widget("button_icon_unknown").connect("clicked", change_icon, "unknown", prefs_tree, treeview, statusIcon, wTree)
    prefs_tree.get_widget("button_icon_apply").connect("clicked", change_icon, "apply", prefs_tree, treeview, statusIcon, wTree)

    prefs = read_configuration()

    prefs_tree.get_widget("visible1").set_active(prefs["level1_visible"])
    prefs_tree.get_widget("visible2").set_active(prefs["level2_visible"])
    prefs_tree.get_widget("visible3").set_active(prefs["level3_visible"])
    prefs_tree.get_widget("visible4").set_active(prefs["level4_visible"])
    prefs_tree.get_widget("visible5").set_active(prefs["level5_visible"])
    prefs_tree.get_widget("safe1").set_active(prefs["level1_safe"])
    prefs_tree.get_widget("safe2").set_active(prefs["level2_safe"])
    prefs_tree.get_widget("safe3").set_active(prefs["level3_safe"])
    prefs_tree.get_widget("safe4").set_active(prefs["level4_safe"])
    prefs_tree.get_widget("safe5").set_active(prefs["level5_safe"])

    prefs_tree.get_widget("timer_minutes_label").set_text(_("minutes"))
    prefs_tree.get_widget("timer_hours_label").set_text(_("hours"))
    prefs_tree.get_widget("timer_days_label").set_text(_("days"))
    prefs_tree.get_widget("timer_minutes").set_value(prefs["timer_minutes"])
    prefs_tree.get_widget("timer_hours").set_value(prefs["timer_hours"])
    prefs_tree.get_widget("timer_days").set_value(prefs["timer_days"])

    prefs_tree.get_widget("text_ping").set_text(prefs["ping_domain"])

    prefs_tree.get_widget("spin_delay").set_value(prefs["delay"])

    prefs_tree.get_widget("checkbutton_dist_upgrade").set_active(prefs["dist_upgrade"])

    prefs_tree.get_widget("image_busy").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_busy, 24, 24))
    prefs_tree.get_widget("image_up2date").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_up2date, 24, 24))
    prefs_tree.get_widget("image_updates").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_updates, 24, 24))
    prefs_tree.get_widget("image_error").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_error, 24, 24))
    prefs_tree.get_widget("image_unknown").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_unknown, 24, 24))
    prefs_tree.get_widget("image_apply").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(g.icon_apply, 24, 24))

    # Blacklisted packages
    treeview_blacklist = prefs_tree.get_widget("treeview_blacklist")
    column1 = gtk.TreeViewColumn(_("Ignored packages"), gtk.CellRendererText(), text=0)
    column1.set_sort_column_id(0)
    column1.set_resizable(True)
    treeview_blacklist.append_column(column1)
    treeview_blacklist.set_headers_clickable(True)
    treeview_blacklist.set_reorderable(False)
    treeview_blacklist.show()

    model = gtk.TreeStore(str)
    model.set_sort_column_id( 0, gtk.SORT_ASCENDING )
    treeview_blacklist.set_model(model)

    if os.path.exists("/etc/linuxmint/mintupdate.ignored"):
        ignored_list = open("/etc/linuxmint/mintupdate.ignored", "r")
        for ignored_pkg in ignored_list:            
            iter = model.insert_before(None, None)
            model.set_value(iter, 0, ignored_pkg.strip())
        del model
        ignored_list.close()
    
    prefs_tree.get_widget("toolbutton_add").connect("clicked", add_blacklisted_package, treeview_blacklist)
    prefs_tree.get_widget("toolbutton_remove").connect("clicked", remove_blacklisted_package, treeview_blacklist)

def quit_cb(widget, window, vpaned, data = None):
    if data:
        data.set_visible(False)
    try:
        g.LOG.writelines("++ Exiting - requested by user\n")
        g.LOG.flush()
        g.LOG.close()
        save_window_size(window, vpaned)
    except:
        pass # cause LOG might already been closed
    # Whatever works best heh :) 
    g.PID = os.getpid()    
    os.system("kill -9 %s &" % g.PID)
    #gtk.main_quit()
    #sys.exit(0)

# treeview-setting
def display_selected_package(selection, wTree):    
    wTree.get_widget("textview_description").get_buffer().set_text("")
    wTree.get_widget("textview_changes").get_buffer().set_text("")            
    (model, iter) = selection.get_selected()
    if (iter != None):
        selected_package = model.get_value(iter, 1)
        description_txt = model.get_value(iter, 8)                
        wTree.get_widget("notebook_details").set_current_page(0)
        wTree.get_widget("textview_description").get_buffer().set_text(description_txt)

# toolbar-setting
def clear(widget, treeView):
    model = treeView.get_model()
    iter = model.get_iter_first()
    while (iter != None):
        model.set_value(iter, 0, "false")
        iter = model.iter_next(iter)
    g.STATUSBAR.push(g.CONTEXT_ID, _("No updates selected"))

def select_all(widget, treeView):
    model = treeView.get_model()
    iter = model.get_iter_first()
    while (iter != None):
        model.set_value(iter, 0, "true")
        iter = model.iter_next(iter)
    iter = model.get_iter_first()
    download_size = 0
    num_selected = 0
    while (iter != None):
        checked = model.get_value(iter, 0)
        if (checked == "true"):            
            size = model.get_value(iter, 9)
            download_size = download_size + size
            num_selected = num_selected + 1                          
        iter = model.iter_next(iter)
    if num_selected == 0:
        g.STATUSBAR.push(g.CONTEXT_ID, _("No updates selected"))
    elif num_selected == 1:
        g.STATUSBAR.push(g.CONTEXT_ID, _("%(selected)d update selected (%(size)s)") % {'selected':num_selected, 'size':size_to_string(download_size)})
    else:
        g.STATUSBAR.push(g.CONTEXT_ID, _("%(selected)d updates selected (%(size)s)") % {'selected':num_selected, 'size':size_to_string(download_size)})

def install(widget, treeView, statusIcon, wTree):
    install = InstallThread(treeView, statusIcon, wTree)
    install.start()

# notebook-setting
def switch_page(notebook, page, page_num, Wtree, treeView):
    selection = treeView.get_selection()
    (model, iter) = selection.get_selected()
    if (iter != None):
        selected_package = model.get_value(iter, 1)
        description_txt = model.get_value(iter, 8)   
        if (page_num == 0):
            # Description tab
            wTree.get_widget("textview_description").get_buffer().set_text(description_txt)
        if (page_num == 1):
            # Changelog tab            
            level = model.get_value(iter, 7)
            version = model.get_value(iter, 4)
            retriever = ChangelogRetriever(selected_package, level, version, wTree)
            retriever.start()

# menubar-setting
def close_window(window, event, vpaned):
    window.hide()
    save_window_size(window, vpaned)
    g.APP_HIDDEN = True
    return True

def hide_window(widget, window):
    window.hide()
    g.APP_HIDDEN = True

def open_repositories(widget):
    if os.path.exists("/usr/bin/software-sources"):
        os.system("/usr/bin/software-sources &")
    elif os.path.exists("/usr/bin/software-properties-gtk"):
        os.system("/usr/bin/software-properties-gtk &")
    elif os.path.exists("/usr/bin/software-properties-kde"):
        os.system("/usr/bin/software-properties-kde &")

def open_history(widget):
    #Set the Glade file
    gladefile = "/usr/lib/linuxmint/mintUpdate/mintUpdate.glade"
    wTree = gtk.glade.XML(gladefile, "window4")
    treeview_update = wTree.get_widget("treeview_history")
    wTree.get_widget("window4").set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")

    wTree.get_widget("window4").set_title(_("History of updates") + " - " + _("Update Manager"))

    # the treeview
    column1 = gtk.TreeViewColumn(_("Date"), gtk.CellRendererText(), text=1)
    column1.set_sort_column_id(1)
    column1.set_resizable(True)
    column2 = gtk.TreeViewColumn(_("Package"), gtk.CellRendererText(), text=2)
    column2.set_sort_column_id(2)
    column2.set_resizable(True)
    column3 = gtk.TreeViewColumn(_("Level"), gtk.CellRendererPixbuf(), pixbuf=3)
    column3.set_sort_column_id(6)
    column3.set_resizable(True)
    column4 = gtk.TreeViewColumn(_("Old version"), gtk.CellRendererText(), text=4)
    column4.set_sort_column_id(4)
    column4.set_resizable(True)
    column5 = gtk.TreeViewColumn(_("New version"), gtk.CellRendererText(), text=5)
    column5.set_sort_column_id(5)
    column5.set_resizable(True)

    treeview_update.append_column(column1)
    treeview_update.append_column(column3)
    treeview_update.append_column(column2)
    treeview_update.append_column(column5)
    treeview_update.append_column(column4)

    treeview_update.set_headers_clickable(True)
    treeview_update.set_reorderable(False)
    treeview_update.set_search_column(2)
    treeview_update.set_enable_search(True)
    treeview_update.show()

    model = gtk.TreeStore(str, str, str, gtk.gdk.Pixbuf, str, str, str) # (date, packageName, level, oldVersion, newVersion, stringLevel)
    if (os.path.exists("/var/log/mintUpdate.history")):
        updates = commands.getoutput("cat /var/log/mintUpdate.history")
        updates = string.split(updates, "\n")
        for pkg in updates:
            values = string.split(pkg, "\t")
            if len(values) == 5:
                date = values[0]
                package = values[1]
                level = values[2]
                oldVersion = values[3]
                newVersion = values[4]

                iter = model.insert_before(None, None)
                model.set_value(iter, 0, package)
                model.row_changed(model.get_path(iter), iter)
                model.set_value(iter, 1, date)
                model.set_value(iter, 2, package)
                model.set_value(iter, 3, gtk.gdk.pixbuf_new_from_file("/usr/lib/linuxmint/mintUpdate/icons/level" + str(level) + ".png"))
                model.set_value(iter, 4, oldVersion)
                model.set_value(iter, 5, newVersion)
                model.set_value(iter, 6, level)

    treeview_update.set_model(model)
    del model
    wTree.get_widget("button_close").connect("clicked", history_cancel, wTree)
    wTree.get_widget("button_clear").connect("clicked", history_clear, treeview_update)

def open_about(widget):
    dlg = gtk.AboutDialog()
    dlg.set_title(_("About") + " - " + _("Update Manager"))
    dlg.set_program_name("mintUpdate")
    dlg.set_comments(_("Update Manager"))
    try:
        h = open('/usr/share/common-licenses/GPL','r')
        s = h.readlines()
        gpl = ""
        for line in s:
            gpl += line
        h.close()
        dlg.set_license(gpl)
    except Exception, detail:
        print detail
    try:
        version = commands.getoutput("/usr/lib/linuxmint/common/version.py mintupdate")
        dlg.set_version(version)
    except Exception, detail:
        print detail

    dlg.set_authors(["Clement Lefebvre <root@linuxmint.com>", "Chris Hodapp <clhodapp@live.com>"])
    dlg.set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
    dlg.set_logo(gtk.gdk.pixbuf_new_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg"))
    def close(w, res):
        if res == gtk.RESPONSE_CANCEL:
            w.hide()
    dlg.connect("response", close)
    dlg.show()

def refresh_status(treeview_update, statusIcon, wTree, pkgs2rm):
    gtk.gdk.threads_enter()
    vpaned_position = wTree.get_widget("vpaned1").get_position()
    gtk.gdk.threads_leave()
    model = treeview_update.get_model()
    iter = model.get_iter_first()
    while (iter != None):
        name = model.get_value(iter, g.model_name)
        if name in pkgs2rm:
            model.remove(iter)
            #del g.pkginfodict[name]
        iter = model.iter_next(iter)

    num_ignored = 0
    num_safe = 0
    download_size = 0

    prefs = read_configuration()
    ignored_list = []
    if os.path.exists("/etc/linuxmint/mintupdate.ignored"):
        blacklist_file = open("/etc/linuxmint/mintupdate.ignored", "r")
        for blacklist_line in blacklist_file:
            ignored_list.append(blacklist_line.strip())
        blacklist_file.close()

    iter = model.get_iter_first()
    while (iter != None):
        name = model.get_value(iter, g.model_name)
        level = model.get_value(iter, g.model_strlevel)
        size = model.get_value(iter, g.model_size)
        for blacklist in ignored_list:
            if fnmatch.fnmatch(name, blacklist):
                num_ignored = num_ignored + 1
                break
        if(prefs["level" + str(level) + "_safe"]): 
            num_safe = num_safe + 1
            download_size = download_size + size
        iter = model.iter_next(iter)

    if (num_safe > 0):
        if (num_safe == 1):
            if (num_ignored == 0):
                statusString = _("1 recommended update available (%(size)s)") % {'size':size_to_string(download_size)}
            elif (num_ignored == 1):
                statusString = _("1 recommended update available (%(size)s), 1 ignored") % {'size':size_to_string(download_size)}
            elif (num_ignored > 1):
                statusString = _("1 recommended update available (%(size)s), %(ignored)d ignored") % {'size':size_to_string(download_size), 'ignored':num_ignored}
        else:
            if (num_ignored == 0):
                statusString = _("%(recommended)d recommended updates available (%(size)s)") % {'recommended':num_safe, 'size':size_to_string(download_size)}
            elif (num_ignored == 1):
                statusString = _("%(recommended)d recommended updates available (%(size)s), 1 ignored") % {'recommended':num_safe, 'size':size_to_string(download_size)}
            elif (num_ignored > 0):
                statusString = _("%(recommended)d recommended updates available (%(size)s), %(ignored)d ignored") % {'recommended':num_safe, 'size':size_to_string(download_size), 'ignored':num_ignored}
    gtk.gdk.threads_enter()
    statusIcon.set_from_file(g.icon_updates)
    statusIcon.set_tooltip(statusString)
    g.STATUSBAR.push(g.CONTEXT_ID, statusString)
    wTree.get_widget("notebook_details").set_current_page(0)
    wTree.get_widget("window1").window.set_cursor(None)
    wTree.get_widget("window1").set_sensitive(True)
    wTree.get_widget("vpaned1").set_position(vpaned_position)
    gtk.gdk.threads_leave()

# other-setting
def change_icon(widget, button, prefs_tree, treeview, statusIcon, wTree):
    dialog = gtk.FileChooserDialog(_("Update Manager"), None, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    filter1 = gtk.FileFilter()
    filter1.set_name("*.*")
    filter1.add_pattern("*")
    filter2 = gtk.FileFilter()
    filter2.set_name("*.png")
    filter2.add_pattern("*.png")
    dialog.add_filter(filter2)
    dialog.add_filter(filter1)

    if dialog.run() == gtk.RESPONSE_OK:
        filename = dialog.get_filename()
        if (button == "busy"):
            prefs_tree.get_widget("image_busy").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_busy = filename
        if (button == "up2date"):
            prefs_tree.get_widget("image_up2date").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_up2date = filename
        if (button == "updates"):
            prefs_tree.get_widget("image_updates").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_updates = filename
        if (button == "error"):
            prefs_tree.get_widget("image_error").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_error = filename
        if (button == "unknown"):
            prefs_tree.get_widget("image_unknown").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_unknown = filename
        if (button == "apply"):
            prefs_tree.get_widget("image_apply").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(filename, 24, 24))
            g.icon_apply = filename
    dialog.destroy()

def pref_apply(widget, prefs_tree, treeview, statusIcon, wTree):

    if (not os.path.exists("/etc/linuxmint")):
        os.system("mkdir -p /etc/linuxmint")
        g.LOG.writelines("++ Creating /etc/linuxmint directory\n")
        g.LOG.flush()

    config = ConfigObj("/etc/linuxmint/mintUpdate.conf")

    #Write level config
    config['levels'] = {}
    config['levels']['level1_visible'] = prefs_tree.get_widget("visible1").get_active()
    config['levels']['level2_visible'] = prefs_tree.get_widget("visible2").get_active()
    config['levels']['level3_visible'] = prefs_tree.get_widget("visible3").get_active()
    config['levels']['level4_visible'] = prefs_tree.get_widget("visible4").get_active()
    config['levels']['level5_visible'] = prefs_tree.get_widget("visible5").get_active()
    config['levels']['level1_safe'] = prefs_tree.get_widget("safe1").get_active()
    config['levels']['level2_safe'] = prefs_tree.get_widget("safe2").get_active()
    config['levels']['level3_safe'] = prefs_tree.get_widget("safe3").get_active()
    config['levels']['level4_safe'] = prefs_tree.get_widget("safe4").get_active()
    config['levels']['level5_safe'] = prefs_tree.get_widget("safe5").get_active()

    #Write refresh config
    config['refresh'] = {}
    config['refresh']['timer_minutes'] = int(prefs_tree.get_widget("timer_minutes").get_value())
    config['refresh']['timer_hours'] = int(prefs_tree.get_widget("timer_hours").get_value())
    config['refresh']['timer_days'] = int(prefs_tree.get_widget("timer_days").get_value())

    #Write update config
    config['update'] = {}
    config['update']['delay'] = str(int(prefs_tree.get_widget("spin_delay").get_value()))
    config['update']['ping_domain'] = prefs_tree.get_widget("text_ping").get_text()
    config['update']['dist_upgrade'] = prefs_tree.get_widget("checkbutton_dist_upgrade").get_active()

    #Write icons config
    config['icons'] = {}
    config['icons']['busy'] = g.icon_busy
    config['icons']['up2date'] = g.icon_up2date
    config['icons']['updates'] = g.icon_updates
    config['icons']['error'] = g.icon_error
    config['icons']['unknown'] = g.icon_unknown
    config['icons']['apply'] = g.icon_apply
    
    #Write blacklisted packages
    ignored_list = open("/etc/linuxmint/mintupdate.ignored", "w")
    treeview_blacklist = prefs_tree.get_widget("treeview_blacklist")
    model = treeview_blacklist.get_model()
    iter = model.get_iter_first()
    while iter is not None:
        pkg = model.get_value(iter, 0)
        iter = model.iter_next(iter)
        ignored_list.writelines(pkg + "\n")
    ignored_list.close()

    config.write()

    prefs_tree.get_widget("window2").hide()
    #t = threading.Thread(target=refresh_status, args=(treeview_update, statusIcon, wTree, []))
    #t.start()
    refresh = RefreshThread(treeview, statusIcon, wTree)
    refresh.start()

def info_cancel(widget, prefs_tree):
    prefs_tree.get_widget("window3").hide()

def history_cancel(widget, tree):
    tree.get_widget("window4").hide()

def history_clear(widget, tree):
    os.system("rm -rf /var/log/mintUpdate.history")
    model = gtk.TreeStore(str, str, str, gtk.gdk.Pixbuf, str, str)
    tree.set_model(model)
    del model

def pref_cancel(widget, prefs_tree):
    prefs_tree.get_widget("window2").hide()

def add_blacklisted_package(widget, treeview_blacklist):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, None)
    dialog.set_markup("<b>" + _("Please enter a package name:") + "</b>")
    dialog.set_title(_("Ignore a package"))
    dialog.set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
    entry = gtk.Entry()
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(_("Package name:")), False, 5, 5)
    hbox.pack_end(entry)
    dialog.format_secondary_markup("<i>" + _("All available upgrades for this package will be ignored.") + "</i>")
    dialog.vbox.pack_end(hbox, True, True, 0)
    dialog.show_all()
    dialog.run()
    name = entry.get_text()
    dialog.destroy()
    pkg = name.strip()
    if pkg != '':
        model = treeview_blacklist.get_model()
        iter = model.insert_before(None, None)
        model.set_value(iter, 0, pkg)

def remove_blacklisted_package(widget, treeview_blacklist):
    selection = treeview_blacklist.get_selection()
    (model, iter) = selection.get_selected()
    if (iter != None):
        pkg = model.get_value(iter, 0)
        model.remove(iter)

def info_cb(widget, data = None):
    if data:
        data.set_visible(False)
    try:
        g.LOG.flush()
        os.system("gedit " + g.LOGFILE)
    except:
        pass

def popup_menu_cb(widget, button, time, data = None):
    if button == 3:
        if data:
            data.show_all()
            data.popup(None, None, gtk.status_icon_position_menu, 3, time, widget)
    pass

def activate_icon_cb(widget, data, wTree):
    if (g.APP_HIDDEN == True):
            # check credentials
        if os.getuid() != 0 :
            try:
                g.LOG.writelines("++ Launching mintUpdate in root mode...\n")
                g.LOG.flush()
                g.LOG.close()
            except:
                pass #cause we might have closed it already

            command = "gksudo --message \"" + _("Please enter your password to start the update manager") + "\" /usr/lib/linuxmint/mintUpdate/mintUpdate.py show &"
            desktop_environnment = commands.getoutput("/usr/lib/linuxmint/common/env_check.sh")
            if (desktop_environnment == "KDE"):
                command = "kdesudo -i /usr/share/linuxmint/logo.png --comment \"" + _("Please enter your password to start the update manager") + "\" -d /usr/lib/linuxmint/mintUpdate/mintUpdate.py show &"
            os.system(command)

        else:
            wTree.get_widget("window1").show()
            g.APP_HIDDEN = False
    else:
        wTree.get_widget("window1").hide()
        g.APP_HIDDEN = True
        save_window_size(wTree.get_widget("window1"), wTree.get_widget("vpaned1"))

def celldatafunction_checkbox(column, cell, model, iter):
    cell.set_property("activatable", True)
    checked = model.get_value(iter, 0)
    if (checked == "true"):
        cell.set_property("active", True)
    else:
        cell.set_property("active", False)

def toggled(renderer, path, treeview):
    model = treeview.get_model()
    iter = model.get_iter(path)
    if (iter != None):
        checked = model.get_value(iter, 0)
        if (checked == "true"):
            model.set_value(iter, 0, "false")
        else:
            model.set_value(iter, 0, "true")
    
    iter = model.get_iter_first()
    download_size = 0
    num_selected = 0
    while (iter != None):
        checked = model.get_value(iter, 0)
        if (checked == "true"):            
            size = model.get_value(iter, g.model_size)
            download_size = download_size + size
            num_selected = num_selected + 1                                
        iter = model.iter_next(iter)
    if num_selected == 0:
        g.STATUSBAR.push(g.CONTEXT_ID, _("No updates selected"))
    elif num_selected == 1:
        g.STATUSBAR.push(g.CONTEXT_ID, _("%(selected)d update selected (%(size)s)") % {'selected':num_selected, 'size':size_to_string(download_size)})
    else:
        g.STATUSBAR.push(g.CONTEXT_ID, _("%(selected)d updates selected (%(size)s)") % {'selected':num_selected, 'size':size_to_string(download_size)})

def save_window_size(window, vpaned):
    config = ConfigObj("/etc/linuxmint/mintUpdate.conf")
    config['dimensions'] = {}
    config['dimensions']['x'] = window.get_size()[0]
    config['dimensions']['y'] = window.get_size()[1]
    config['dimensions']['pane_position'] = vpaned.get_position()
    config.write()

def setVisibleColumn(checkmenuitem, column, configName):
    config = ConfigObj("/etc/linuxmint/mintUpdate.conf")
    if (config.has_key('visible_columns')):
        config['visible_columns'][configName] = checkmenuitem.get_active()
    else:
        config['visible_columns'] = {}
        config['visible_columns'][configName] = checkmenuitem.get_active()
    config.write()
    column.set_visible(checkmenuitem.get_active())
