# Library for Version Flow (VerFlow) project

# version of the library
__version__ = "0.1.0"

# importing standard libraries
import argparse
import os
import collections
import configparser
import sys
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch
import hashlib
from math import ceil
import re
import zlib

#importing other files

argparser = argparse.ArgumentParser(description='VerFlow: VCS for Coding Projects')  # creating an argument parser object
argsubparsers = argparser.add_subparsers(title='Commands', dest='command')  # creating a subparser object
argsubparsers.required = True  # subparser is required

#subparser for cmd_init handler

argsp = argsubparsers.add_parser("init",help="Initialize a new, empty repository")
argsp.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository"
                   )

import os
import configparser


class VerFlowRepository(object):
    """A git repository"""

    # initializing the git repository
    worktree = None
    gitDir = None
    conf = None

    # utility function for repository path
    def repoPath(self, *path):
        return os.path.join(self.gitDir, *path)

    def repoFile(self, *path, mkdir=False):
        if self.repoDir(*path[:-1], mkdir=mkdir):
            return self.repoPath(*path)

    def repoDir(self, *path, mkdir=False):
        path = self.repoPath(*path)

        if os.path.exists(path):
            if os.path.isdir(path):
                return path
            else:
                raise Exception("Not a directory %s" % path)

        if mkdir:
            os.makedirs(path)
            return path
        else:
            return None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitDir = os.path.join(path, '.git')

        # checking if the path is a git repository
        if not (force or os.path.isdir(self.gitDir)):
            raise Exception("Not a VerFlow repository %s" % path)

        # reading the configuration file
        self.conf = configparser.ConfigParser()
        cf = self.repoFile('config')

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get('core', 'repositoryformatversion'))
            if vers != 0:
                raise Exception("Unsupported repositoryformatversion %s" % vers)

    def repoCreate(self,path):
        repo = VerFlowRepository(path, True)  # repository object
        # validating the directory
        if os.path.exists(repo.worktree):
            if not os.path.isdir(repo.worktree):
                raise Exception("%s is not a directory!" % path)
            if os.path.exists(repo.gitDir) and os.listdir(repo.gitDir):
                raise Exception("%s Already contains a git repository!" % path)
        else:
            os.makedirs(repo.worktree)

        assert repo.repoDir("branches", mkdir=True)
        assert repo.repoDir("objects",mkdir=True)
    
        #.git/description
        with open(repo.repoFile("description"),"w") as f:
            f.write("Unnamed Repository. Edit this file 'description' to name the repository. \n")

        #.git/HEAD
        with open(repo.repoFile("HEAD"),"w") as f:
            f.write("ref: refs/heads/master\n")
        
        with open(repo.repoFile("config"), "w") as f:
            config = repo.repoDefaultConfig()
            config.write(f)

        return repo
    def repoDefaultConfig(self):
        conf = configparser.ConfigParser()

        conf.add_section("core")
        conf.set("core","repositoryFormatVersion" , "0")
        conf.set("core", "filemode","false")
        conf.set("core","bare","false")

        return conf

def main(argv = sys.argv[1:]):
    args = argparser.parse_args(argv)
    if args.command == "init"        : cmd_init(args)
    # match the command
    # match args.command:
    #     case "add":
    #         cmd_add(args)
    #     case "commit":
    #         cmd_commit(args)
    #     case "checkout":
    #         cmd_checkout(args)
    #     case "log":
    #         cmd_log(args)
    #     case "cat-file":
    #         cmd_cat_file(args)
    #     case "init":
    #         cmd_init(args)
    #     case "check-ignore":
    #         cmd_check_ignore(args)
    #     case "hash-object":
    #         cmd_hash_object(args)
    #     case "ls-files":
    #         cmd_ls_files(args)
    #     case "ls-tree":
    #         cmd_ls_tree(args)
    #     case "rev-parse":
    #         cmd_rev_parse(args)
    #     case "rm":
    #         cmd_rm(args)
    #     case "show-ref":
    #         cmd_show_ref(args)
    #     case "status":
    #         cmd_status(args)
    #     case "tag":
    #         cmd_tag(args)
    #     case _:
    #         argparser.print("Bad Command")

#cmd_init handler
def cmd_init(args):
    VerFlowRepository.repoCreate(args.path)
