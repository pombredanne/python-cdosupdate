#!/usr/bin/env python
# coding: utf-8
import gtk
import time
import threading
import os
import commands
import fnmatch
import tempfile
from configobj import ConfigObj
from subprocess import Popen, PIPE
import globalParameter as g
from getPackagesInfo import checkAPT

gtk.gdk.threads_init()

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

class RefreshThread(threading.Thread):
    def __init__(self, treeview_update, wTree):
        threading.Thread.__init__(self)
        self.treeview_update = treeview_update
        self.wTree = wTree

    def run(self):
        gtk.gdk.threads_enter()
        vpaned_position = self.wTree.get_widget("vpaned1").get_position()
        gtk.gdk.threads_leave()
        try:
            g.LOG.writelines("++ Starting refresh\n")
            g.LOG.flush()
            gtk.gdk.threads_enter()
            g.STATUSBAR.push(g.CONTEXT_ID, _("Starting refresh..."))
            self.wTree.get_widget("window1").window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.wTree.get_widget("window1").set_sensitive(False)
            self.wTree.get_widget("label_error_detail").set_text("")
            self.wTree.get_widget("hbox_error").hide()
            self.wTree.get_widget("scrolledwindow1").hide()
            self.wTree.get_widget("viewport1").hide()
            self.wTree.get_widget("label_error_detail").hide()
            self.wTree.get_widget("image_error").hide()
            # Starts the blinking
            g.STATUSICON.set_from_file(g.icon_busy)
            g.STATUSICON.set_tooltip(_("Checking for updates"))
            self.wTree.get_widget("vpaned1").set_position(vpaned_position)
            #g.STATUSICON.set_blinking(True)
            gtk.gdk.threads_leave()

            model = gtk.TreeStore(str, str, gtk.gdk.Pixbuf, str, str, int, str, str, object, str, str) # (check, packageName, level, oldVersion, newVersion, size, stringSize, stringLevel, description, warning, extrainfo)
            model.set_sort_column_id(7, gtk.SORT_ASCENDING )         

            prefs = read_configuration()
            
            # Check to see if no other APT process is running
            p1 = Popen(['ps', '-U', 'root', '-o', 'comm'], stdout=PIPE)
            p = p1.communicate()[0]
            running = False
            pslist = p.split('\n')
            for process in pslist:
                if process.strip() in ["dpkg", "apt-get","synaptic","update-manager", "adept", "adept-notifier"]:
                    running = True
                    break
            if (running == True):
                gtk.gdk.threads_enter()
                g.STATUSICON.set_from_file(g.icon_unknown)
                g.STATUSICON.set_tooltip(_("Another application is using APT"))
                g.STATUSBAR.push(g.CONTEXT_ID, _("Another application is using APT"))
                g.LOG.writelines("-- Another application is using APT\n")
                g.LOG.flush()
                #g.STATUSICON.set_blinking(False)
                self.wTree.get_widget("window1").window.set_cursor(None)
                self.wTree.get_widget("window1").set_sensitive(True)
                gtk.gdk.threads_leave()
                return False

            gtk.gdk.threads_enter()
            g.STATUSBAR.push(g.CONTEXT_ID, _("Finding the list of updates..."))
            self.wTree.get_widget("vpaned1").set_position(vpaned_position)
            gtk.gdk.threads_leave()

            pkgsname = []
            if g.APP_HIDDEN:
                pkgs2update = checkAPT(False, 0)
            else:
                pkgs2update = checkAPT(True, self.wTree.get_widget("window1").window.xid)
            pkgsname = pkgs2update.keys()
            #print "have get apt info."

            # Check return value
            if ("ERROR" in pkgsname):
                error_msg = commands.getoutput("/usr/lib/linuxmint/mintUpdate/checkAPT.py")
                gtk.gdk.threads_enter()
                g.STATUSICON.set_from_file(g.icon_error)
                g.STATUSICON.set_tooltip(_("Could not refresh the list of packages"))
                g.STATUSBAR.push(g.CONTEXT_ID, _("Could not refresh the list of packages"))
                g.LOG.writelines("-- Error in checkAPT.py, could not refresh the list of packages\n")
                g.LOG.flush()
                self.wTree.get_widget("label_error_detail").set_text(error_msg)
                self.wTree.get_widget("label_error_detail").show()
                self.wTree.get_widget("viewport1").show()
                self.wTree.get_widget("scrolledwindow1").show()
                self.wTree.get_widget("image_error").show()
                self.wTree.get_widget("hbox_error").show()
                #g.STATUSICON.set_blinking(False)
                self.wTree.get_widget("window1").window.set_cursor(None)
                self.wTree.get_widget("window1").set_sensitive(True)
                #g.STATUSBAR.push(g.CONTEXT_ID, _(""))
                gtk.gdk.threads_leave()
                return False
            # Check value and Look for mintupdate
            if ("mintupdate" in pkgsname):
                new_mintupdate = True
            else:
                new_mintupdate = False
            
            # Look at the packages one by one
            num_visible = 0
            num_safe = 0            
            download_size = 0
            num_ignored = 0

            if (len(pkgsname) == None):
                g.STATUSICON.set_from_file(g.icon_up2date)
                g.STATUSICON.set_tooltip(_("Your system is up to date"))
                g.STATUSBAR.push(g.CONTEXT_ID, _("Your system is up to date"))
                g.LOG.writelines("++ System is up to date\n")
                g.LOG.flush()
            else:
                ignored_list = []
                if os.path.exists("/etc/linuxmint/mintupdate.ignored"):
                    blacklist_file = open("/etc/linuxmint/mintupdate.ignored", "r")
                    for blacklist_line in blacklist_file:
                        ignored_list.append(blacklist_line.strip())
                    blacklist_file.close()
                rulesAll=[]
                if os.path.exists("/usr/lib/linuxmint/mintUpdate/rules"):
                    rulesFile = open("/usr/lib/linuxmint/mintUpdate/rules","r")
                    rulesLine = rulesFile.readlines()
                    for line in rulesLine:
                        rulesAll.append(line.split("|"))
                    rulesFile.close()
                
                for pkg in pkgsname:
                    packageIsBlacklisted = False
                    for blacklist in ignored_list:
                        if fnmatch.fnmatch(pkg, blacklist):
                            num_ignored = num_ignored + 1
                            packageIsBlacklisted = True
                            break

                    if packageIsBlacklisted:
                        continue
                    label = pkgs2update[pkg].label
                    newVersion = pkgs2update[pkg].newVersion
                    oldVersion = pkgs2update[pkg].oldVersion
                    size = int(pkgs2update[pkg].size)
                    description = pkgs2update[pkg].description
                    strSize = size_to_string(size)

                    level = 3 # Level 3 by default
                    extraInfo = ""
                    warning = ""
                    #rulesFile = open("/usr/lib/linuxmint/mintUpdate/rules","r")
                    #rules = rulesFile.readlines()
                    foundVersionRule = False
                    foundPackageRule = False # whether we found a rule with the exact package name or not
                    if(label == g.CDOS_LABEL):
                        level = 1
                        extraInfo = "packages from CDOS."
                        warning = "package from CDOS."
                    else:
                        for rules in rulesAll:
                            if (foundVersionRule == False):
                                rule_package = rules[0]
                                rule_version = rules[1]
                                rule_level = rules[2]
                                rule_extraInfo = rules[3]
                                rule_warning = rules[4]
                                if (rule_package == pkg):
                                    foundPackageRule = True
                                    if (rule_version == newVersion):
                                        level = rule_level
                                        extraInfo = rule_extraInfo
                                        warning = rule_warning
                                        foundVersionRule = True # We found a rule with the exact package name and version, no need to look elsewhere
                                    else:
                                        if (rule_version == "*"):
                                            level = rule_level
                                            extraInfo = rule_extraInfo
                                            warning = rule_warning
                                else:
                                    if (rule_package.startswith("*")):
                                        keyword = rule_package.replace("*", "")
                                        index = pkg.find(keyword)
                                        if (index > -1 and foundPackageRule == False):
                                            level = rule_level
                                            extraInfo = rule_extraInfo
                                            warning = rule_warning

                    level = int(level)
                    if (prefs["level" + str(level) + "_visible"]):
                        if (new_mintupdate):
                            if (pkg == "mintupdate"):
                                iter = model.insert_before(None, None)
                                model.set_value(iter, g.model_check, "true")
                                model.row_changed(model.get_path(iter), iter)
                                model.set_value(iter, g.model_name, pkg)
                                model.set_value(iter, g.model_levelpix, gtk.gdk.pixbuf_new_from_file("/usr/lib/linuxmint/mintUpdate/icons/level" + str(level) + ".png"))
                                model.set_value(iter, g.model_oldversion, oldVersion)
                                model.set_value(iter, g.model_newversion, newVersion)
                                model.set_value(iter, g.model_size, size)
                                model.set_value(iter, g.model_strsize, strSize)
                                model.set_value(iter, g.model_strlevel, str(level))
                                model.set_value(iter, g.model_des, description)
                                model.set_value(iter, g.model_warning, warning)
                                model.set_value(iter, g.model_extrainfo, extraInfo)
                                #model.set_value(iter, 11, sourcePackage)
                                num_visible = num_visible + 1
                            #else:
                            #    model.set_value(iter, 0, "false")
                        else:
                            iter = model.insert_before(None, None)
                            #print "path:", model.get_path(iter)
                            if (prefs["level" + str(level) + "_safe"]):
                                #model.set_value(iter, g.model_check, "true")
                                num_safe = num_safe + 1
                                download_size = download_size + size
                            else:
                                model.set_value(iter, g.model_check, "false")
                            model.row_changed(model.get_path(iter), iter)
                            model.set_value(iter, g.model_name, pkg)
                            model.set_value(iter, g.model_levelpix, gtk.gdk.pixbuf_new_from_file("/usr/lib/linuxmint/mintUpdate/icons/level" + str(level) + ".png"))
                            model.set_value(iter, g.model_oldversion, oldVersion)
                            model.set_value(iter, g.model_newversion, newVersion)
                            model.set_value(iter, g.model_size, size)
                            model.set_value(iter, g.model_strsize, strSize)
                            model.set_value(iter, g.model_strlevel, str(level))
                            model.set_value(iter, g.model_des, description)
                            model.set_value(iter, g.model_warning, warning)
                            model.set_value(iter, g.model_extrainfo, extraInfo)
                            #model.set_value(iter, 11, sourcePackage)#
                            num_visible = num_visible + 1

                gtk.gdk.threads_enter()  
                if (new_mintupdate):
                    self.statusString = _("A new version of the update manager is available")
                    g.STATUSICON.set_from_file(g.icon_updates)
                    g.STATUSICON.set_tooltip(self.statusString)
                    g.STATUSBAR.push(g.CONTEXT_ID, self.statusString)
                    g.LOG.writelines("++ Found a new version of mintupdate\n")
                    g.LOG.flush()
                else:
                    if (num_safe > 0):
                        if (num_safe == 1):
                            if (num_ignored == 0):
                                self.statusString = _("1 recommended update available (%(size)s)") % {'size':size_to_string(download_size)}
                            elif (num_ignored == 1):
                                self.statusString = _("1 recommended update available (%(size)s), 1 ignored") % {'size':size_to_string(download_size)}
                            elif (num_ignored > 1):
                                self.statusString = _("1 recommended update available (%(size)s), %(ignored)d ignored") % {'size':size_to_string(download_size), 'ignored':num_ignored}
                        else:
                            if (num_ignored == 0):
                                self.statusString = _("%(recommended)d recommended updates available (%(size)s)") % {'recommended':num_safe, 'size':size_to_string(download_size)}
                            elif (num_ignored == 1):
                                self.statusString = _("%(recommended)d recommended updates available (%(size)s), 1 ignored") % {'recommended':num_safe, 'size':size_to_string(download_size)}
                            elif (num_ignored > 0):
                                self.statusString = _("%(recommended)d recommended updates available (%(size)s), %(ignored)d ignored") % {'recommended':num_safe, 'size':size_to_string(download_size), 'ignored':num_ignored}
                        g.STATUSICON.set_from_file(g.icon_updates)
                        g.STATUSICON.set_tooltip(self.statusString)
                        g.STATUSBAR.push(g.CONTEXT_ID, self.statusString)
                        g.LOG.writelines("++ Found " + str(num_safe) + " recommended software updates\n")
                        g.LOG.flush()
                    else:
                        g.STATUSICON.set_from_file(g.icon_up2date)
                        g.STATUSICON.set_tooltip(_("Your system is up to date"))
                        g.STATUSBAR.push(g.CONTEXT_ID, _("Your system is up to date"))
                        g.LOG.writelines("++ System is up to date\n")
                        g.LOG.flush()

            g.LOG.writelines("++ Refresh finished\n")
            g.LOG.flush()
            # Stop the blinking
            #g.STATUSICON.set_blinking(False)
            self.wTree.get_widget("notebook_details").set_current_page(0)
            self.wTree.get_widget("window1").window.set_cursor(None)
            self.treeview_update.set_model(model)
            del model
            self.wTree.get_widget("window1").set_sensitive(True)
            self.wTree.get_widget("vpaned1").set_position(vpaned_position)
            gtk.gdk.threads_leave()

        except Exception, detail:
            print "-- Exception occured in the refresh thread: " + str(detail)
            g.LOG.writelines("-- Exception occured in the refresh thread: " + str(detail) + "\n")
            g.LOG.flush()
            gtk.gdk.threads_enter()
            g.STATUSICON.set_from_file(g.icon_error)
            g.STATUSICON.set_tooltip(_("Could not refresh the list of packages"))
            #g.STATUSICON.set_blinking(False)
            self.wTree.get_widget("window1").window.set_cursor(None)
            self.wTree.get_widget("window1").set_sensitive(True)
            g.STATUSBAR.push(g.CONTEXT_ID, _("Could not refresh the list of packages"))
            self.wTree.get_widget("vpaned1").set_position(vpaned_position)
            gtk.gdk.threads_leave()

    def checkDependencies(self, changes, cache):
        foundSomething = False
        for pkg in changes:
            for dep in pkg.candidateDependencies:
                for o in dep.or_dependencies:
                    try:
                        if cache[o.name].isUpgradable:
                            pkgFound = False
                            for pkg2 in changes:
                                if o.name == pkg2.name:
                                    pkgFound = True
                            if pkgFound == False:
                                newPkg = cache[o.name]
                                changes.append(newPkg)
                                foundSomething = True
                    except Exception, detail:
                        pass # don't know why we get these..
        if (foundSomething):
            changes = self.checkDependencies(changes, cache)
        return changes

class InstallThread(threading.Thread):

    def __init__(self, treeView, wTree):
        threading.Thread.__init__(self)
        self.treeView = treeView
        self.wTree = wTree

    def run(self):
        try:
            g.LOG.writelines("++ Install requested by user\n")
            g.LOG.flush()
            gtk.gdk.threads_enter()
            self.wTree.get_widget("window1").window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.wTree.get_widget("window1").set_sensitive(False)
            installNeeded = False
            packages = []
            model = self.treeView.get_model()
            gtk.gdk.threads_leave()

            iter = model.get_iter_first()
            history = open("/var/log/mintUpdate.history", "a")
            while (iter != None):
                checked = model.get_value(iter, 0)
                if (checked == "true"):
                    installNeeded = True
                    package = model.get_value(iter, 1)
                    level = model.get_value(iter, 7)
                    oldVersion = model.get_value(iter, 3)
                    newVersion = model.get_value(iter, 4)
                    history.write(commands.getoutput('date +"%Y.%m.%d %H:%M:%S"') + "\t" + package + "\t" + level + "\t" + oldVersion + "\t" + newVersion + "\n")
                    packages.append(package)
                    g.LOG.writelines("++ Will install " + str(package) + "\n")
                    g.LOG.flush()
                iter = model.iter_next(iter)
            history.close()

            if (installNeeded == True):
                proceed = True
                try:
                    pkgs = ' '.join(str(pkg) for pkg in packages)
                    warnings = commands.getoutput("/usr/lib/linuxmint/mintUpdate/checkWarnings.py %s" % pkgs)
                    #print ("/usr/lib/linuxmint/mintUpdate/checkWarnings.py %s" % pkgs)
                    warnings = warnings.split("###")
                    if len(warnings) == 2:
                        installations = warnings[0].split()
                        removals = warnings[1].split()
                        if len(installations) > 0 or len(removals) > 0:
                            gtk.gdk.threads_enter()
                            try:
                                dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, None)
                                dialog.set_title("")
                                dialog.set_markup("<b>" + _("This upgrade will trigger additional changes") + "</b>")
                                #dialog.format_secondary_markup("<i>" + _("All available upgrades for this package will be ignored.") + "</i>")
                                dialog.set_icon_from_file("/usr/lib/linuxmint/mintUpdate/icons/base.svg")
                                dialog.set_default_size(640, 480)
                                
                                if len(removals) > 0:
                                    # Removals
                                    label = gtk.Label()
                                    if len(removals) == 1:
                                        label.set_text(_("The following package will be removed:"))
                                    else:
                                        label.set_text(_("The following %d packages will be removed:") % len(removals))
                                    label.set_alignment(0, 0.5)
                                    scrolledWindow = gtk.ScrolledWindow()
                                    scrolledWindow.set_shadow_type(gtk.SHADOW_IN)
                                    scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                                    treeview = gtk.TreeView()
                                    column1 = gtk.TreeViewColumn("", gtk.CellRendererText(), text=0)
                                    column1.set_sort_column_id(0)
                                    column1.set_resizable(True)
                                    treeview.append_column(column1)
                                    treeview.set_headers_clickable(False)
                                    treeview.set_reorderable(False)
                                    treeview.set_headers_visible(False)
                                    model = gtk.TreeStore(str)
                                    removals.sort()
                                    for pkg in removals:
                                        iter = model.insert_before(None, None)
                                        model.set_value(iter, 0, pkg)
                                    treeview.set_model(model)
                                    treeview.show()
                                    scrolledWindow.add(treeview)
                                    dialog.vbox.add(label)
                                    dialog.vbox.add(scrolledWindow)
                                
                                if len(installations) > 0:
                                    # Installations
                                    label = gtk.Label()
                                    if len(installations) == 1:
                                        label.set_text(_("The following package will be installed:"))
                                    else:
                                        label.set_text(_("The following %d packages will be installed:") % len(installations))
                                    label.set_alignment(0, 0.5)
                                    scrolledWindow = gtk.ScrolledWindow()
                                    scrolledWindow.set_shadow_type(gtk.SHADOW_IN)
                                    scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                                    treeview = gtk.TreeView()
                                    column1 = gtk.TreeViewColumn("", gtk.CellRendererText(), text=0)
                                    column1.set_sort_column_id(0)
                                    column1.set_resizable(True)
                                    treeview.append_column(column1)
                                    treeview.set_headers_clickable(False)
                                    treeview.set_reorderable(False)
                                    treeview.set_headers_visible(False)
                                    model = gtk.TreeStore(str)
                                    installations.sort()
                                    for pkg in installations:
                                        iter = model.insert_before(None, None)
                                        model.set_value(iter, 0, pkg)
                                    treeview.set_model(model)
                                    treeview.show()
                                    scrolledWindow.add(treeview)   
                                    dialog.vbox.add(label)
                                    dialog.vbox.add(scrolledWindow)
                                
                                dialog.show_all()
                                if dialog.run() == gtk.RESPONSE_OK:
                                    proceed = True
                                else: 
                                    proceed = False
                                dialog.destroy()  
                            except Exception, detail:
                                print detail
                            gtk.gdk.threads_leave()   
                        else:
                            proceed = True
                except Exception, details: 
                    print details
                                                                       
                if proceed:
                    gtk.gdk.threads_enter()
                    g.STATUSICON.set_from_file(g.icon_apply)
                    g.STATUSICON.set_tooltip(_("Installing updates"))
                    gtk.gdk.threads_leave()
                    
                    g.LOG.writelines("++ Ready to launch synaptic\n")
                    g.LOG.flush()
                    cmd = ["sudo", "/usr/sbin/synaptic", "--hide-main-window",  \
                            "--non-interactive", "--parent-window-id", "%s" % self.wTree.get_widget("window1").window.xid]
                    cmd.append("-o")
                    cmd.append("Synaptic::closeZvt=false")
                    cmd.append("--progress-str")
                    cmd.append("\"" + _("Please wait, this can take some time") + "\"")
                    cmd.append("--finish-str")
                    cmd.append("\"" + _("Update is complete") + "\"")
                    f = tempfile.NamedTemporaryFile()

                    for pkg in packages:
                        f.write("%s\tinstall\n" % pkg)
                    cmd.append("--set-selections-file")
                    cmd.append("%s" % f.name)
                    f.flush()
                    comnd = Popen(' '.join(cmd), stdout=g.LOG, stderr=g.LOG, shell=True)
                    returnCode = comnd.wait()
                    g.LOG.writelines("++ Return code:" + str(returnCode) + "\n")
                    #sts = os.waitpid(comnd.PID, 0)
                    f.close()
                    g.LOG.writelines("++ Install finished\n")
                    g.LOG.flush()

                    #gtk.gdk.threads_enter()
                    #global g.APP_HIDDEN
                    #g.APP_HIDDEN = True
                    #self.wTree.get_widget("window1").hide()
                    #gtk.gdk.threads_leave()

                    if "mintupdate" in packages:
                        # Restart
                        try:
                            g.LOG.writelines("++ Mintupdate was updated, restarting it in root mode...\n")
                            g.LOG.flush()
                            g.LOG.close()
                        except:
                            pass #cause we might have closed it already

                        command = "gksudo --message \"" + _("Please enter your password to start the update manager") + "\" /usr/lib/linuxmint/mintUpdate/mintUpdate.py show &"                        
                        if ("KDE" in commands.getoutput("grep DESKTOP /etc/linuxmint/info")):
                            command = "kdesudo -i /usr/share/linuxmint/logo.png --comment \"" + _("Please enter your password to start the update manager") + "\" -d /usr/lib/linuxmint/mintUpdate/mintUpdate.py show &"
                        os.system(command)

                    else:
                        if(returnCode == 0):
                            self.refresh_status(self.treeView, self.wTree, packages)
                        else:
                            # Refresh
                            gtk.gdk.threads_enter()
                            g.STATUSICON.set_from_file(g.icon_busy)
                            g.STATUSICON.set_tooltip(_("Checking for updates"))
                            self.wTree.get_widget("window1").window.set_cursor(None)
                            self.wTree.get_widget("window1").set_sensitive(True)
                            gtk.gdk.threads_leave()
                            refresh = RefreshThread(self.treeView, self.wTree)
                            refresh.start()
                else:
                    # Stop the blinking but don't refresh
                    gtk.gdk.threads_enter()
                    self.wTree.get_widget("window1").window.set_cursor(None)
                    self.wTree.get_widget("window1").set_sensitive(True)
                    gtk.gdk.threads_leave()
            else:
                # Stop the blinking but don't refresh
                gtk.gdk.threads_enter()
                self.wTree.get_widget("window1").window.set_cursor(None)
                self.wTree.get_widget("window1").set_sensitive(True)
                gtk.gdk.threads_leave()

        except Exception, detail:
            g.LOG.writelines("-- Exception occured in the install thread: " + str(detail) + "\n")
            g.LOG.flush()
            gtk.gdk.threads_enter()
            g.STATUSICON.set_from_file(g.icon_error)
            g.STATUSICON.set_tooltip(_("Could not install the security updates"))
            g.LOG.writelines("-- Could not install security updates\n")
            g.LOG.flush()
            #g.STATUSICON.set_blinking(False)
            self.wTree.get_widget("window1").window.set_cursor(None)
            self.wTree.get_widget("window1").set_sensitive(True)
            gtk.gdk.threads_leave()

    def refresh_status(self, treeview_update, wTree, pkgs2rm):
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
        g.STATUSICON.set_from_file(g.icon_updates)
        g.STATUSICON.set_tooltip(statusString)
        g.STATUSBAR.push(g.CONTEXT_ID, statusString)
        wTree.get_widget("notebook_details").set_current_page(0)
        wTree.get_widget("window1").window.set_cursor(None)
        wTree.get_widget("window1").set_sensitive(True)
        wTree.get_widget("vpaned1").set_position(vpaned_position)
        gtk.gdk.threads_leave()


class ChangelogRetriever(threading.Thread):
    def __init__(self, source_package, level, version, wTree):
        threading.Thread.__init__(self)
        self.source_package = source_package
        self.level = level 
        self.version = version
        self.wTree = wTree
           
    def run(self):         
        gtk.gdk.threads_enter()
        self.wTree.get_widget("textview_changes").get_buffer().set_text(_("Downloading changelog..."))  
        gtk.gdk.threads_leave()       
        
        changelog_sources = []
        changelog_sources.append("http://packages.linuxmint.com/dev/" + self.source_package + "_" + self.version + "_amd64.changes")
        changelog_sources.append("http://packages.linuxmint.com/dev/" + self.source_package + "_" + self.version + "_i386.changes")                
        if (self.source_package.startswith("lib")):
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/main/%s/%s/%s_%s/changelog" % (self.source_package[0:4], self.source_package, self.source_package, self.version))        
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/multiverse/%s/%s/%s_%s/changelog" % (self.source_package[0:4], self.source_package, self.source_package, self.version))
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/universe/%s/%s/%s_%s/changelog" % (self.source_package[0:4], self.source_package, self.source_package, self.version))        
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/restricted/%s/%s/%s_%s/changelog" % (self.source_package[0:4], self.source_package, self.source_package, self.version))
        else:
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/main/%s/%s/%s_%s/changelog" % (self.source_package[0], self.source_package, self.source_package, self.version))        
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/multiverse/%s/%s/%s_%s/changelog" % (self.source_package[0], self.source_package, self.source_package, self.version))
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/universe/%s/%s/%s_%s/changelog" % (self.source_package[0], self.source_package, self.source_package, self.version))        
            changelog_sources.append("http://changelogs.ubuntu.com/changelogs/pool/restricted/%s/%s/%s_%s/changelog" % (self.source_package[0], self.source_package, self.source_package, self.version))
        
        changelog = _("No changelog available")
        
        for changelog_source in changelog_sources:
            try:                      
                print "Trying to fetch the changelog from: %s" % changelog_source
                url = urllib2.urlopen(changelog_source, None, 30)
                source = url.read()
                url.close()
                
                changelog = ""
                if "linuxmint.com" in changelog_source:
                    changes = source.split("\n")
                    for change in changes:
                        change = change.strip()
                        if change.startswith("*"):
                            changelog = changelog + change + "\n"
                else:
                    changelog = source                
                break
            except:
                pass
                                        
        gtk.gdk.threads_enter()                
        self.wTree.get_widget("textview_changes").get_buffer().set_text(changelog)        
        gtk.gdk.threads_leave()

class AutomaticRefreshThread(threading.Thread):
    def __init__(self, treeView, wTree):
        threading.Thread.__init__(self)
        self.treeView = treeView
        self.wTree = wTree

    def run(self):
        try:
            while(True):
                prefs = read_configuration()
                timer = (prefs["timer_minutes"] * 60) + (prefs["timer_hours"] * 60 * 60) + (prefs["timer_days"] * 24 * 60 * 60)

                try:
                    g.LOG.writelines("++ Auto-refresh timer is going to sleep for " + str(prefs["timer_minutes"]) + " minutes, " + str(prefs["timer_hours"]) + " hours and " + str(prefs["timer_days"]) + " days\n")
                    g.LOG.flush()
                except:
                    pass # cause it might be closed already
                timetosleep = int(timer)
                if (timetosleep == 0):
                    time.sleep(60) # sleep 1 minute, don't mind the config we don't want an infinite loop to go nuts :)
                else:
                    time.sleep(timetosleep)
                    if (g.APP_HIDDEN == True):
                        try:
                            g.LOG.writelines("++ MintUpdate is in tray mode, performing auto-refresh\n")
                            g.LOG.flush()
                        except:
                            pass # cause it might be closed already
                        # Refresh
                        refresh = RefreshThread(self.treeView, self.wTree)
                        refresh.start()
                    else:
                        try:
                            g.LOG.writelines("++ The mintUpdate window is open, skipping auto-refresh\n")
                            g.LOG.flush()
                        except:
                            pass # cause it might be closed already

        except Exception, detail:
            try:
                g.LOG.writelines("-- Exception occured in the auto-refresh thread.. so it's probably dead now: " + str(detail) + "\n")
                g.LOG.flush()
            except:
                pass # cause it might be closed already

