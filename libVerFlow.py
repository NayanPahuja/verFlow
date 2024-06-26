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
## Subparser for cmd_cat-file handler
argsp = argsubparsers.add_parser("cat-file",help="Output content of repository objects")
argsp.add_argument("type",
                   metavar="type",
                   choices=["blob","commit","tree","tag"],
                   help="Specify the type of object")
argsp.add_argument("object",
                   metavar="object",
                   help="Object to display")

##Subparser for cmd_hash-object handler
argsp = argsubparsers.add_parser("hash-object", help="Hash and compute object ID, optionally creates a blob from a file")
argsp.add_argument("-t",
                   metavar="type",
                   dest="type",
                   choices=["blob","commit","tree","tag"],
                   default="blob",
                   help="Specify the object type")
argsp.add_argument("-w",
                   dest="write",
                   action = "store_true",
                   help="Write the object back to database")
argsp.add_argument("path",
                   help="Read the object from <file>")

## Subparser for cmd_log handler

argsp = argsubparsers.add_parser("log",help="Display the history of a given commit")
argsp.add_argument("commit",
                   default="HEAD",
                   nargs="?",
                   help="Commits to start the log at.")

## Subparser for cmd ls tree

argsp = argsubparsers.add_parser("ls-tree",help="Print a tree object")
argsp.add_argument("-r",
                   dest="recursive",
                   action="store_true",
                   help='Recurse into sub-trees')
argsp.add_argument("tree", help="A tree object")

## Subparser for cmd_checkout

argsp = argsubparsers.add_parser("checkout",help="Checkout to commit inside of a directory")

argsp.add_argument("commit",
                   help="The commit or tree to checkout")
argsp.add_argument("path",
                   help="The empty dir to checkout on")

## Subparser for cmd_show_refs

argsp = argsubparsers.add_parser("show-refs",help="List the references created! ")


## Subparser for cmd_tag

argsp = argsubparsers.add_parser("tag",help="List and Create tags")

argsp.add_argument("-a",
                   action="store_true",
                   dest="createTagObject",
                   help="Whether to create a tag object")

argsp.add_argument("name",
                   nargs="?",
                   help="The new tag's name")

argsp.add_argument("object",
                   default="HEAD",
                   nargs="?",
                   help="The object the tag will point to")

## Subparser for rev-parse command

argsp = argsubparsers.add_parser("rev-parse", help="Parse revision (or other objects) identifiers")

argsp.add_argument("--vf-type",
                   metavar="type",
                   dest="type",
                   choices=["blob","commit","tag","tree"],
                   default=None,
                   help="Specify the expected type")
argsp.add_argument("name",
                   help="The name to parse")


argsp = argsubparsers.add_parser("ls-files", help= "List all the files currently in staging area")

argsp.add_argument("--verbose",
                   action="store_true",help="Show everything")

# Subparser for check-ignore command 

argsp = argsubparsers.add_parser("check-ignore",
                                 help="Check path(s) against ignore rules")
argsp.add_argument("path",
                   nargs="+",
                   help="Path to check")
# Subparser for  status command
argsp = argsubparsers.add_parser("status",
                                 help= "Show the current status of worktree")

# SubParser for rm command
argsp = argsubparsers.add_parser("rm",help="Remove files from the working tree and the index")
argsp.add_argument("path",
                   nargs="+",
                   help="Path of files to remove")
# Subparser for add command
argsp = argsubparsers.add_parser("add", help= "Add files contents to the index")
argsp.add_argument("path", nargs="+", help="Files to add")

# Subparser for commit command
argsp = argsubparsers.add_parser("commit", help= "Record changes to the repository.")
argsp.add_argument("-m",
                   metavar="message",
                   dest="message",
                   help="Message to associate with this commit")

def main(argv = sys.argv[1:]):
    args = argparser.parse_args(argv)
    commandBridge.handle_command(args)