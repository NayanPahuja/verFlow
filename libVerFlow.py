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
import commandBridge
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
    commandBridge.handle_command(args)