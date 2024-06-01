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
import verFlowRepository

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
    verFlowRepository.repoCreate(args.path)
