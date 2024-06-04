# commandBridge.py

import argparse
import sys
import os
from verFlowRepository import repoCreate, repoFile, repoFind, repoPath, repoDir, repoDefaultConfig
from object import objectRead, objectFind, objectWrite
from object import GitBlob, GitCommit
from kvlmParser import kvlmParse, kvlmSerialize

""" INITIALIZE THE REPOSITORY || CREATE THE REPO """
def cmd_init(args):
    repoCreate(args.path)

"""Output the contents of a file(type object) to stdout"""
def cmd_cat_file(args):
    repo = repoFind()
    cat_file(repo,args.object,fmt = args.type.encode())

def cat_file(repo,obj,fmt = None):
    obj = objectRead(repo,objectFind(repo,obj,fmt = fmt))
    sys.stdout.buffer.write(obj.serialize())
"""Hash the object and write back(optional)"""
def cmd_hash_object(args):
    if args.write:
        repo = repoFind()
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

### log command using graphviz
def cmd_log(args):
    repo = repoFind()

    print("Graph of verFlow Log{")
    print(" node[shape = rect]")
    logGraphviz(repo,objectFind(repo,args.commit), set())
    print("}")

def logGraphviz(repo, sha, commitSeen):

    if sha in commitSeen:
        return
    commitSeen.add(sha)

    commit = objectRead(repo,sha)
    shortHash = sha[0:8]
    message = commit.kvlm[None].decode("utf-8").strip()
    message = message.replace("\\", "\\\\")
    message  = message.replace("\"", "\\\"")

    

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
