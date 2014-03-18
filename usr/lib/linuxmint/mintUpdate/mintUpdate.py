#!/usr/bin/env python

try:
    import os
    import commands
    import sys
    import string
    import gtk
    import gtk.glade
    import tempfile
    import threading
    import time
    import gettext
    import fnmatch
    import urllib2
    #from user import home
    sys.path.append('/usr/lib/linuxmint/common')
    import globalParameter as g
    from updateCDOS import update_cdos
    from updateCallbacks import *
    from updateClasses import RefreshThread
    from updateClasses import AutomaticRefreshThread
except Exception, detail:
    print detail
    pass

try:
    import pygtk
    pygtk.require("2.0")
except Exception, detail:
    print detail
    pass

try:
    numMintUpdate = commands.getoutput("ps -A | grep mintUpdate | wc -l")
    if (numMintUpdate != "0"):
        if (os.getuid() == 0):
            os.system("killall mintUpdate")
        else:
            print "Another mintUpdate is already running, exiting."
            sys.exit(1)
except Exception, detail:
    print detail

architecture = commands.getoutput("uname -a")
if (architecture.find("x86_64") >= 0):
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15, 'mintUpdate', 0, 0, 0)
else:
    import dl
    if os.path.exists('/lib/libc.so.6'):
        libc = dl.open('/lib/libc.so.6')
        libc.call('prctl', 15, 'mintUpdate', 0, 0, 0)
    elif os.path.exists('/lib/i386-linux-gnu/libc.so.6'):
        libc = dl.open('/lib/i386-linux-gnu/libc.so.6')
        libc.call('prctl', 15, 'mintUpdate', 0, 0, 0)

# i18n
gettext.install("mintupdate", "/usr/lib/linuxmint/mintUpdate/locale")

# i18n for menu item
menuName = _("Update Manager")
menuGenericName = _("Software Updates")
menuComment = _("Show and install available updates")


# global-function



gtk.gdk.threads_init()
#parentPid = "0"
#if len(sys.argv) > 2:
#    parentPid = sys.argv[2]
#    if (parentPid != "0"):
#        os.system("kill -9 " + parentPid)
#

# prepare the log
g.PID = os.getpid()

if not os.path.exists(g.LOGDIR):
    os.system("mkdir -p " + g.LOGDIR)
    os.system("chmod a+rwx " + g.LOGDIR)
    
if os.getuid() == 0 :
    os.system("chmod a+rwx " + g.LOGDIR)
    g.MODE = "root"
else:
    g.MODE = "user"

g.LOG = tempfile.NamedTemporaryFile(prefix = g.LOGDIR, delete=False)
g.LOGFILE = g.LOG.name
try:
    os.system("chmod a+rw %s" % g.LOG.name)
except Exception, detail:
    print detail

g.LOG.writelines("++ Launching mintUpdate in " + g.MODE + " g.MODE\n")
g.LOG.flush()

try:

    prefs = read_configuration()

    #Set the Glade file
    gladefile = "/usr/lib/linuxmint/mintUpdate/mintUpdate.glade"
    wTree = gtk.glade.XML(gladefile, "window1")
    wTree.get_widget("window1").set_title(_("Update Manager"))
    wTree.get_widget("window1").set_default_size(prefs['dimensions_x'], prefs['dimensions_y'])
    wTree.get_widget("vpaned1").set_position(prefs['dimensions_pane_position'])
    
    g.STATUSBAR = wTree.get_widget("statusbar")
    g.CONTEXT_ID = g.STATUSBAR.get_context_id("mintUpdate")
    vbox = wTree.get_widget("vbox_main")
    treeview_update = wTree.get_widget("treeview_update")
    wTree.get_widget("window1").set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
    wTree.get_widget("window1").connect("delete_event", close_window, wTree.get_widget("vpaned1"))

    # Get the window socket (needed for synaptic later on)    
    if os.getuid() != 0 :
        # If we're not in root mode do that (don't know why it's needed.. very weird)
        socket = gtk.Socket()
        vbox.pack_start(socket, True, True, 0)
        socket.show()
        window_id = repr(socket.get_id())

    # statusicon-setting
    statusIcon = gtk.StatusIcon()
    statusIcon.set_from_file(g.icon_busy)
    statusIcon.set_tooltip(_("Checking for updates"))
    statusIcon.set_visible(True)
    menu = gtk.Menu()
    menuItem3 = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
    menuItem3.connect('activate', force_refresh, treeview_update, statusIcon, wTree)
    menu.append(menuItem3)
    menuItem2 = gtk.ImageMenuItem(gtk.STOCK_DIALOG_INFO)
    menuItem2.connect('activate', open_information)
    menu.append(menuItem2)
    if os.getuid() == 0 :
        menuItem4 = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        menuItem4.connect('activate', open_preferences, treeview_update, statusIcon, wTree)
        menu.append(menuItem4)
    menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
    menuItem.connect('activate', quit_cb, wTree.get_widget("window1"), wTree.get_widget("vpaned1"), statusIcon)
    menu.append(menuItem)
    statusIcon.connect('activate', activate_icon_cb, None, wTree)
    statusIcon.connect('popup-menu', popup_menu_cb, menu)

    # treeview-setting
    cr = gtk.CellRendererToggle()
    cr.connect("toggled", toggled, treeview_update)
    column1 = gtk.TreeViewColumn(_("Upgrade"), cr)
    column1.set_cell_data_func(cr, celldatafunction_checkbox)
    #column1.set_sort_column_id(5)
    column1.set_resizable(True)
    column2 = gtk.TreeViewColumn(_("Package"), gtk.CellRendererText(), text=1)
    column2.set_sort_column_id(1)
    column2.set_resizable(True)
    column3 = gtk.TreeViewColumn(_("Level"), gtk.CellRendererPixbuf(), pixbuf=2)
    column3.set_sort_column_id(7)
    column3.set_resizable(True)
    column4 = gtk.TreeViewColumn(_("Old version"), gtk.CellRendererText(), text=3)
    column4.set_sort_column_id(3)
    column4.set_resizable(True)
    column5 = gtk.TreeViewColumn(_("New version"), gtk.CellRendererText(), text=4)
    column5.set_sort_column_id(4)
    column5.set_resizable(True)
    column6 = gtk.TreeViewColumn(_("Size"), gtk.CellRendererText(), text=6)
    column6.set_sort_column_id(5)
    column6.set_resizable(True)
    treeview_update.append_column(column3)
    treeview_update.append_column(column1)
    treeview_update.append_column(column2)
    treeview_update.append_column(column5)
    treeview_update.append_column(column4)
    treeview_update.append_column(column6)
    treeview_update.set_headers_clickable(True)
    treeview_update.set_reorderable(False)
    treeview_update.show()
    #model = gtk.TreeStore(str, str, gtk.gdk.Pixbuf, str, str, str, str, str, int)
    model = gtk.TreeStore(str, str, gtk.gdk.Pixbuf, str, str, int, str, str, object, str, str)
    #model.set_sort_column_id( 7, gtk.SORT_ASCENDING )
    treeview_update.set_model(model)
    del model
    treeview_update.connect( "button-release-event", menuPopup, treeview_update, statusIcon, wTree )
    selection = treeview_update.get_selection()
    selection.connect("changed", display_selected_package, wTree)

    # toolbar-setting
    wTree.get_widget("tool_clear").connect("clicked", clear, treeview_update)
    wTree.get_widget("tool_select_all").connect("clicked", select_all, treeview_update)
    wTree.get_widget("tool_refresh").connect("clicked", force_refresh, treeview_update, statusIcon, wTree)
    wTree.get_widget("tool_apply").connect("clicked", install, treeview_update, statusIcon, wTree)
    wTree.get_widget("update_cdos").connect("clicked", update_cdos, treeview_update, statusIcon, wTree)
    wTree.get_widget("notebook_details").connect("switch-page", switch_page, wTree, treeview_update)

    # menubar-setting
    fileMenu = gtk.MenuItem(_("_File"))
    fileSubmenu = gtk.Menu()
    fileMenu.set_submenu(fileSubmenu)
    closeMenuItem = gtk.ImageMenuItem(gtk.STOCK_CLOSE)
    closeMenuItem.get_child().set_text(_("Close"))
    closeMenuItem.connect("activate", hide_window, wTree.get_widget("window1"))
    fileSubmenu.append(closeMenuItem)

    editMenu = gtk.MenuItem(_("_Edit"))
    editSubmenu = gtk.Menu()
    editMenu.set_submenu(editSubmenu)
    prefsMenuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
    prefsMenuItem.get_child().set_text(_("Preferences"))
    prefsMenuItem.connect("activate", open_preferences, treeview_update, statusIcon, wTree)
    editSubmenu.append(prefsMenuItem)
    if os.path.exists("/usr/bin/software-sources") or os.path.exists("/usr/bin/software-properties-gtk") or os.path.exists("/usr/bin/software-properties-kde"):
        sourcesMenuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        sourcesMenuItem.set_image(gtk.image_new_from_file("/usr/lib/linuxmint/mintUpdate/icons/software-properties.png"))
        sourcesMenuItem.get_child().set_text(_("Software sources"))
        sourcesMenuItem.connect("activate", open_repositories)
        editSubmenu.append(sourcesMenuItem)

    viewMenu = gtk.MenuItem(_("_View"))
    viewSubmenu = gtk.Menu()
    viewMenu.set_submenu(viewSubmenu)
    historyMenuItem = gtk.ImageMenuItem(gtk.STOCK_INDEX)
    historyMenuItem.get_child().set_text(_("History of updates"))
    historyMenuItem.connect("activate", open_history)
    infoMenuItem = gtk.ImageMenuItem(gtk.STOCK_DIALOG_INFO)
    infoMenuItem.get_child().set_text(_("Information"))
    infoMenuItem.connect("activate", open_information)
    visibleColumnsMenuItem = gtk.MenuItem(gtk.STOCK_DIALOG_INFO)
    visibleColumnsMenuItem.get_child().set_text(_("Visible columns"))
    visibleColumnsMenu = gtk.Menu()
    visibleColumnsMenuItem.set_submenu(visibleColumnsMenu)

    levelColumnMenuItem = gtk.CheckMenuItem(_("Level"))
    levelColumnMenuItem.set_active(prefs["level_column_visible"])
    column3.set_visible(prefs["level_column_visible"])
    levelColumnMenuItem.connect("toggled", setVisibleColumn, column3, "level")
    visibleColumnsMenu.append(levelColumnMenuItem)

    packageColumnMenuItem = gtk.CheckMenuItem(_("Package"))
    packageColumnMenuItem.set_active(prefs["package_column_visible"])
    column2.set_visible(prefs["package_column_visible"])
    packageColumnMenuItem.connect("toggled", setVisibleColumn, column2, "package")
    visibleColumnsMenu.append(packageColumnMenuItem)

    oldVersionColumnMenuItem = gtk.CheckMenuItem(_("Old version"))
    oldVersionColumnMenuItem.set_active(prefs["old_version_column_visible"])
    column4.set_visible(prefs["old_version_column_visible"])
    oldVersionColumnMenuItem.connect("toggled", setVisibleColumn, column4, "old_version")
    visibleColumnsMenu.append(oldVersionColumnMenuItem)

    newVersionColumnMenuItem = gtk.CheckMenuItem(_("New version"))
    newVersionColumnMenuItem.set_active(prefs["new_version_column_visible"])
    column5.set_visible(prefs["new_version_column_visible"])
    newVersionColumnMenuItem.connect("toggled", setVisibleColumn, column5, "new_version")
    visibleColumnsMenu.append(newVersionColumnMenuItem)

    sizeColumnMenuItem = gtk.CheckMenuItem(_("Size"))
    sizeColumnMenuItem.set_active(prefs["size_column_visible"])
    column6.set_visible(prefs["size_column_visible"])
    sizeColumnMenuItem.connect("toggled", setVisibleColumn, column6, "size")
    visibleColumnsMenu.append(sizeColumnMenuItem)

    viewSubmenu.append(visibleColumnsMenuItem)
    viewSubmenu.append(historyMenuItem)
    viewSubmenu.append(infoMenuItem)

    helpMenu = gtk.MenuItem(_("_Help"))
    helpSubmenu = gtk.Menu()
    helpMenu.set_submenu(helpSubmenu)
    aboutMenuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
    aboutMenuItem.get_child().set_text(_("About"))
    aboutMenuItem.connect("activate", open_about)
    helpSubmenu.append(aboutMenuItem)

    #browser.connect("activate", browser_callback)
    #browser.show()
    wTree.get_widget("menubar1").append(fileMenu)
    wTree.get_widget("menubar1").append(editMenu)
    wTree.get_widget("menubar1").append(viewMenu)
    wTree.get_widget("menubar1").append(helpMenu)


    # Set text for all visible widgets (because of i18n)
    wTree.get_widget("tool_clear").set_label(_("Clear"))
    wTree.get_widget("tool_select_all").set_label(_("Select All"))
    wTree.get_widget("tool_refresh").set_label(_("Refresh"))
    wTree.get_widget("tool_apply").set_label(_("Install Updates"))
    wTree.get_widget("update_cdos").set_label(_("System Updates"))
    wTree.get_widget("update_cdos").set_tooltip_text(_("Customization for System"))
    wTree.get_widget("label9").set_text(_("Description"))
    wTree.get_widget("label8").set_text(_("Changelog"))
    wTree.get_widget("label_error_detail").set_text("")
    wTree.get_widget("hbox_error").hide()
    wTree.get_widget("scrolledwindow1").hide()
    wTree.get_widget("viewport1").hide()
    wTree.get_widget("label_error_detail").hide()
    wTree.get_widget("image_error").hide()
    wTree.get_widget("vpaned1").set_position(prefs['dimensions_pane_position'])

    if len(sys.argv) > 1:
        showWindow = sys.argv[1]
        if (showWindow == "show"):
            wTree.get_widget("window1").show_all()
            wTree.get_widget("label_error_detail").set_text("")
            wTree.get_widget("hbox_error").hide()
            wTree.get_widget("scrolledwindow1").hide()
            wTree.get_widget("viewport1").hide()
            wTree.get_widget("label_error_detail").hide()
            wTree.get_widget("image_error").hide()
            wTree.get_widget("vpaned1").set_position(prefs['dimensions_pane_position'])
            g.APP_HIDDEN = False

    if os.getuid() != 0 :        
        #test the network connection to delay mintUpdate in case we're not yet connected
        g.LOG.writelines("++ Testing initial connection\n")
        g.LOG.flush()
        try:
            from urllib import urlopen
            url=urlopen("http://google.com")
            url.read()
            url.close()
            g.LOG.writelines("++ Connection to the Internet successful (tried to read http://www.google.com)\n")
            g.LOG.flush()
        except Exception, detail:
            print detail
            if os.system("ping " + prefs["ping_domain"] + " -c1 -q"):
                g.LOG.writelines("-- No connection found (tried to read http://www.google.com and to ping " + prefs["ping_domain"] + ") - sleeping for " + str(prefs["delay"]) + " seconds\n")
                g.LOG.flush()
                time.sleep(prefs["delay"])
            else:
                g.LOG.writelines("++ Connection found - checking for updates\n")
                g.LOG.flush()


    wTree.get_widget("notebook_details").set_current_page(0)

    refresh = RefreshThread(treeview_update, statusIcon, wTree)
    refresh.start()

    auto_refresh = AutomaticRefreshThread(treeview_update, statusIcon, wTree)
    auto_refresh.start()
    gtk.main()

except Exception, detail:
    print detail
    g.LOG.writelines("-- Exception occured in main thread: " + str(detail) + "\n")
    g.LOG.flush()
    g.LOG.close()
