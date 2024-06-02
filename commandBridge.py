# commandBridge.py

import argparse
import sys
import os
import verFlowRepository as vfrepo
from object import objectRead, objectFind, objectWrite
from object import GitBlob

""" INITIALIZE THE REPOSITORY || CREATE THE REPO """
def cmd_init(args):
    vfrepo.repoCreate(args.path)

"""Output the contents of a file(type object) to stdout"""
def cmd_cat_file(args):
    repo = vfrepo.repoFind()
    cat_file(repo,args.object,fmt = args.type.encode())

def cat_file(repo,obj,fmt = None):
    objectRead(repo,objectFind(repo,obj,fmt = fmt))
    sys.stdout.buffer.write(obj.serialize())
"""Hash the object and write back(optional)"""
def cmd_hash_object(args):
    if args.write:
        repo = vfrepo.repoFind()
    else:
        repo = None

    with open (args.path,"rb") as fd:
        sha = objectHash(fd,args.type.encode(),repo)
        print(sha)

def objectHash(fd,fmt,repo = None):
    data = fd.read()
    
    match fmt:
        case b'commit' : obj = GitCommit(data)
        case b'blob' : obj = GitBlob(data)
        case b'tree' : obj = GitTree(data)
        case b'tag' : obj = GitTag(data)
        case _: raise Exception("Unknown type %s!" % fmt)

    return objectWrite(obj,repo)

### Add Packfile Implementation with index optional




def cmd_add(args):
    # Placeholder function
    pass

def cmd_commit(args):
    # Placeholder function
    pass

def cmd_checkout(args):
    # Placeholder function
    pass

# ... other command functions

# Function to map command to handler
def handle_command(args):
    if args.command == "init":
        cmd_init(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "commit":
        cmd_commit(args)
    elif args.command == "checkout":
        cmd_checkout(args)
    elif args.command == "cat-file":
        cmd_cat_file(args)
    else:
        raise ValueError("Unknown command: {}".format(args.command))
