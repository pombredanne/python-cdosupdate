#!/usr/bin/env python
# coding: utf-8
import os
import sys
import apt
import itertools
from globalParameter import *

class pkginfo():
    def __init__(self, pid, pname, pfullname, candidate, installed):
        self.id = pid
        #print "pid:", pid
        self.name = pname
        self.fullname = pfullname
        self.candidate_info = {}
        self.installed_info = {}
        self.getVersionInfo(candidate, self.candidate_info)
        self.getVersionInfo(installed, self.installed_info)
        #print "self.candidate_info:", self.candidate_info
        #print "self.installed_info:", self.installed_info
        self.newVersion = self.candidate_info['version']
        self.size = self.candidate_info['size']
        self.description = self.candidate_info['description'].replace('\n\n', '\n')
        origin = self.candidate_info['origins'][0]
        self.label = origin['label']
        self.origin = origin['origin']

        self.oldVersion = self.installed_info['version']

    def getVersionInfo(self, version, pdict):
        pdict['version'] = version.version
        pdict['architecture'] = version.architecture
        pdict['size'] = version.size
        pdict['installed_size'] = version.installed_size
        pdict['md5'] = version.md5
        pdict['uri'] = version.uri
        pdict['uris'] = version.uris
        pdict['downloadable'] = version.downloadable
        #pdict['section'] = version.section
        #pdict['priority'] = version.priority
        #pdict['source_name'] = version.source_name
        #pdict['source_version'] = version.source_version
        pdict['description'] = version.description

        #tmp = version.origins[0]
        #pdict['label'] = tmp.label
        #pdict['origin'] = tmp.origin
        #pdict['site'] = tmp.site
        #pdict['component'] = tmp.component
        #pdict['archive'] = tmp.archive
        #pdict['trusted'] = tmp.trusted
        #pdict['origins'] = []
        origins_tuple = []
        for tmp in version.origins:
            origin = {}
            origin['label'] = tmp.label
            origin['origin'] = tmp.origin
            origin['site'] = tmp.site
            origin['component'] = tmp.component
            origin['archive'] = tmp.archive
            origin['trusted'] = tmp.trusted
            origins_tuple.append(origin)
        pdict['origins'] = origins_tuple

    def printInfo(self):
        try:
            info = []
            info.append("软件名(id)：%s(%d)" % (self.name, self.id))
            info.append("软件包名：" + self.fullname)
            info.append("版本：" + self.installed_info['version'])
            info.append("大小：" + str(self.installed_info['size']))
            info.append("MD5值：" + self.installed_info['md5'])
            info.append("下载地址：" + str(self.installed_info['uri']))
            origins = self.installed_info['origins']
            origin = origins[0]
            info.append("源信息：(%s-%s)" % (origin['label'], origin['origin']))
            info.append("----------新软件包信息----------")
            info.append("版本：" + self.candidate_info['version'])
            info.append("大小：" + str(self.candidate_info['size']))
            info.append("MD5值：" + self.candidate_info['md5'])
            #info.append("下载地址：" + str(self.candidate_info['uris']))
            origins = self.candidate_info['origins']
            uris = self.candidate_info['uris']
            if(len(origins) > 1):
                info.append("注意有" + str(len(origins)) +"个源可以选择：")
            #for origin uri in itertools.izip(origins, uris):
            for origin in origins:
                info.append("源信息：(%s-%s)" % (origin['label'], origin['origin']))
                #info.append("下载地址：" + str(uri))
            for uri in uris:
                info.append("下载地址：" + str(uri))

            infos=''
            for tmp in info:
                infos = infos + tmp + "\n"
            return infos
        except Exception, detail:
            return detail

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
        #changes = checkDependencies(changes, cache)

        for pkg in changes:
            if (pkg.is_installed and pkg.marked_upgrade):
                #package = pkg.name
                newVersion = pkg.candidate.version
                oldVersion = pkg.installed.version
                #size = pkg.candidate.size
                #sourcePackage = pkg.candidate.source_name
                #description = pkg.candidate.description
                #description = description.replace('\n\n', '\n')
                #label = pkg.candidate.origins[0].label
                #origin = pkg.candidate.origins[0].origin
                #site = pkg.candidate.origins[0].site
                if (newVersion != oldVersion):
                    info = pkginfo(pkg.id, pkg.name, pkg.fullname, pkg.candidate, pkg.installed)
                    #info.name = package
                    #info.newVersion = newVersion
                    #info.oldVersion = oldVersion
                    #info.size = size
                    #info.sourcePackage = sourcePackage
                    #info.description = description
                    #info.label = label
                    #info.origin = origin
                    #info.site = site
                    pkginfodict[pkg.name] = info
                    #resultString = u"UPDATE###%s###%s###%s###%s###%s###%s" % (package, newVersion, oldVersion, size, sourcePackage, description)
                    #print resultString.encode('ascii', 'xmlcharrefreplace');
        #print pkginfodict.keys(), len(pkginfodict.keys())
        #print 'count:', cnt
    except Exception, detail:
        print "ERROR###ERROR###ERROR###ERROR###ERROR###ERROR###ERROR"
        print detail
        #info = pkginfo()
        pkginfodict['ERROR'] = None 
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
