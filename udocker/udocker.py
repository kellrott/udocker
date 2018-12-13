#!/usr/bin/env python2

# -*- coding: utf-8 -*-
"""
========
udocker
========
Wrapper to execute basic docker containers without using docker.
This tool is a last resort for the execution of docker containers
where docker is unavailable. It only provides a limited set of
functionalities.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
import os

from udocker.cmdparser import CmdParser
from udocker.msg import Msg
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.cli import Udocker
from udocker.utils.fileutil import FileUtil


__author__ = "udocker@lip.pt"
__copyright__ = "Copyright 2017, LIP"
__credits__ = ["PRoot http://proot.me",
               "runC https://runc.io",
               "Fakechroot https://github.com/dex4er/fakechroot",
               "Singularity http://singularity.lbl.gov"
              ]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = '2.0.0-dev3'


class Main(object):
    """Get options, parse and execute the command line"""

    def __init__(self):
        self.cmdp = CmdParser()
        parseok = self.cmdp.parse(sys.argv)
        if not parseok and not self.cmdp.get("--version", "GEN_OPT"):
            Msg().err("Error: parsing command line, use: udocker help")
            sys.exit(1)
        if not (os.geteuid() or self.cmdp.get("--allow-root", "GEN_OPT")):
            Msg().err("Error: do not run as root !")
            sys.exit(1)
        Config().user_init(self.cmdp.get("--config=", "GEN_OPT")) # read config
        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            Config.verbose_level = Msg.DBG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or
              self.cmdp.get("-q", "GEN_OPT")):
            Config.verbose_level = Msg.MSG
        Msg().setlevel(Config.verbose_level)
        if self.cmdp.get("--insecure", "GEN_OPT"):
            Config.http_insecure = True
        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            Config.topdir = self.cmdp.get("--repo=", "GEN_OPT")
            if not LocalRepository(Config.topdir).is_repo():
                Msg().err("Error: invalid udocker repository:",
                          Config.topdir)
                sys.exit(1)
        self.localrepo = LocalRepository(Config.topdir)
        if (self.cmdp.get("", "CMD") == "version" or
                self.cmdp.get("--version", "GEN_OPT")):
            Udocker(self.localrepo).do_version(self.cmdp)
            sys.exit(0)
        if not self.localrepo.is_repo():
            Msg().out("Info: creating repo: " + Config.topdir, l=Msg.INF)
            self.localrepo.create_repo()
        self.udocker = Udocker(self.localrepo)

    def execute(self):
        """Command parsing and selection"""
        cmds = {
            "version": self.udocker.do_version,
            "help": self.udocker.do_help, "search": self.udocker.do_search,
            "images": self.udocker.do_images, "pull": self.udocker.do_pull,
            "create": self.udocker.do_create, "ps": self.udocker.do_ps,
            "run": self.udocker.do_run,
            "rmi": self.udocker.do_rmi, "mkrepo": self.udocker.do_mkrepo,
            "import": self.udocker.do_import, "load": self.udocker.do_load,
            "export": self.udocker.do_export, "clone": self.udocker.do_clone,
            "protect": self.udocker.do_protect, "rm": self.udocker.do_rm,
            "name": self.udocker.do_name, "rmname": self.udocker.do_rmname,
            "verify": self.udocker.do_verify, "logout": self.udocker.do_logout,
            "unprotect": self.udocker.do_unprotect,
            "inspect": self.udocker.do_inspect, "login": self.udocker.do_login,
            "setup":self.udocker.do_setup, "install":self.udocker.do_install,
        }
        if (self.cmdp.get("--help", "GEN_OPT") or
                self.cmdp.get("-h", "GEN_OPT")):
            self.udocker.do_help(self.cmdp)
            return 0
        else:
            command = self.cmdp.get("", "CMD")
            if command in cmds:
                if command != "install":
                    cmds["install"](None)
                if self.cmdp.get("--help") or self.cmdp.get("-h"):
                    self.udocker.do_help(self.cmdp, cmds)   # help on command
                    return 0
                status = cmds[command](self.cmdp)     # executes the command
                if self.cmdp.missing_options():
                    Msg().err("Error: syntax error at: %s" %
                              " ".join(self.cmdp.missing_options()))
                    return 1
                if isinstance(status, bool):
                    return not status
                elif isinstance(status, (int, long)):
                    return status                     # return command status
            else:
                Msg().err("Error: invalid command:", command, "\n")
                self.udocker.do_help(self.cmdp)
        return 1

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self.execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil().cleanup()
            return 1
        except:
            FileUtil().cleanup()
            raise
        else:
            FileUtil().cleanup()
            return exit_status

if __name__ == "__main__":
    sys.exit(Main().start())
