#!/usr/bin/env python

import os
import sys
import apt
from globalParameter import *

class pkginfo():
    pass


#pkginfodict={}
def checkAPT(use_synaptic, window_id):
#    pkginfodict={}
    try:
        cache = apt.Cache()
        
        if os.getuid() == 0 :
#            use_synaptic = False
#            if (len(sys.argv) > 1):
#                if sys.argv[1] == "--use-synaptic":
#                    use_synaptic = True

            if use_synaptic:
                from subprocess import Popen, PIPE
                cmd = ["sudo", "/usr/sbin/synaptic", "--hide-main-window", "--update-at-startup", "--non-interactive", "--parent-window-id", "%s" % window_id]
                #cmd.append("--progress-str")
                #cmd.append("\"" + _("Please wait, this can take some time") + "\"")
                comnd = Popen(' '.join(cmd), shell=True)
                returnCode = comnd.wait()
                #sts = os.waitpid(comnd.pid, 0)            
            else:
                cache.update()

        sys.path.append('/usr/lib/linuxmint/common')
        from configobj import ConfigObj
        config = ConfigObj("/etc/linuxmint/mintUpdate.conf")
        try:
            if (config['update']['dist_upgrade'] == "True"):
                dist_upgrade = True
            else:
                dist_upgrade = False
        except:
            dist_upgrade = True
            
        # Reopen the cache to reflect any updates
        cache.open(None)
        cache.upgrade(dist_upgrade)
        changes = cache.get_changes()
        #print "length of changes:", len(changes)
        
        # Add dependencies
        #changes = checkDependencies(changes, cache)
        for pkg in changes:
            if (pkg.is_installed and pkg.marked_upgrade):
                package = pkg.name
                newVersion = pkg.candidate.version
                oldVersion = pkg.installed.version
                size = pkg.candidate.size
                sourcePackage = pkg.candidate.source_name
                description = pkg.candidate.description
                description = description.replace('\n\n', '\n')
                origin = pkg.candidate.origins[0].origin
                site = pkg.candidate.origins[0].site
                if (newVersion != oldVersion):
                    info = pkginfo()
                    info.name = package
                    info.newVersion = newVersion
                    info.oldVersion = oldVersion
                    info.size = size
                    info.sourcePackage = sourcePackage
                    info.description = description
                    info.origin = origin
                    info.site = site
                    pkginfodict[info.name] = info
                    #resultString = u"UPDATE###%s###%s###%s###%s###%s###%s" % (package, newVersion, oldVersion, size, sourcePackage, description)
                    #print resultString.encode('ascii', 'xmlcharrefreplace');
        #print pkginfodict.keys(), len(pkginfodict.keys())
        #print 'count:', cnt
    except Exception, detail:
        print "ERROR###ERROR###ERROR###ERROR###ERROR###ERROR###ERROR"
        print detail
        info = pkginfo()
        pkginfodict['ERROR'] = info 
    return pkginfodict


#def checkDependencies(changes, cache):
#    foundSomething = False
#    for pkg in changes:
#        for dep in pkg.candidateDependencies:
#            for o in dep.or_dependencies:
#                try:
#                    if cache[o.name].isUpgradable:
#                        pkgFound = False
#                        for pkg2 in changes:
#                            if o.name == pkg2.name:
#                                pkgFound = True
#                        if pkgFound == False:
#                            newPkg = cache[o.name]
#                            changes.append(newPkg)
#                            foundSomething = True
#                except Exception, detail:
#                    pass # don't know why we get these..
#    if (foundSomething):
#        changes = checkDependencies(changes, cache)
#    return changes
