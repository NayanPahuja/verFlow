# commandBridge.py
import collections
import argparse
import sys
import os
import grp, pwd
from datetime import datetime
from verFlowRepository import repoCreate, repoFile, repoFind, repoPath, repoDir, repoDefaultConfig
from object import objectRead, objectFind, objectWrite
from object import GitBlob, GitCommit, GitTree, GitTag
from kvlmParser import kvlmParse, kvlmSerialize
from vfRefs import refsList, refResolver
from vf_indexFile import indexRead
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

    if "\n" in message:
        message = message[:message.index('\n')]
    
    print("  c_{0} [label=\"{1}: {2}\"]".format(sha, sha[0:7], message))
    assert commit.fmt==b'commit'

    if not b'parent' in commit.kvlm.keys():
        #Initial Commit
        return
    
    parents = commit.kvlm[b'parent']
    if type(parents) != list:
        parents = [ parents ]

    for p in parents:
        p = p.decode("ascii")
        print ("  c_{0} -> c_{1};".format(sha, p))
        logGraphviz(repo, p, commitSeen)
    

def cmd_ls_tree(args):
    repo  = repoFind()
    ls_tree(repo,args.tree, args.recursive)

def ls_tree(repo, ref, recursive = None, prefix = ""):
    sha = objectFind(repo, ref, fmt=b"tree")
    obj = objectRead(repo,sha)

    for item in obj.items:
        if len(item.mode)  == 5:
            type = item.mode[0:1]
        else:
            type = item.moode[0:2]

        match type: # Determine the type.
            case b'04': type = "tree"
            case b'10': type = "blob" # A regular file.
            case b'12': type = "blob" # A symlink. Blob contents is link target.
            case b'16': type = "commit" # A submodule
            case _: raise Exception("Weird tree leaf mode {}".format(item.mode))

        if not (recursive and type=='tree'): # This is a leaf
            print("{0} {1} {2}\t{3}".format(
                "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                #ls-tree displays the type
                # of the object pointed to.  
                type,
                item.sha,
                os.path.join(prefix, item.path)))
        else: # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


def cmd_checkout(args):

    repo = repoFind()
    
    obj = objectRead(repo, objectFind(repo,args.commit))


    # If the object is a commit, we grab its tree
    if obj.fmt == b"commit":
        obj = objectRead(repo, obj.kvlm[b'tree'].decode("ascii"))

    #Verify the path exists

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory {0}!".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty {0}!".format(args.path))
    else:
        os.makedirs(args.path)

    treeCheckout(repo,obj, os.path.realpath(args.path))


def treeCheckout(repo, tree, path):

    for item in tree.items:
        obj = objectRead(repo, item.sha)
        dest = os.path.join(path,item.path)


        if obj.fmt == b'tree':
            os.mkdir(dest)
            treeCheckout(repo, obj, dest)
        elif obj.fmt == b'blob':
            # @TODO Support symlinks (identified by mode 12****)
            with open(dest, 'wb') as f:
                f.write(obj.blobdata)

def cmd_show_ref(args):
    repo = repoFind()
    refs = refsList(repo)

    showRefs(repo, refs, prefix="refs")

def showRefs(repo, refs, with_hash = True, prefix = ""):
    for k,v in refs.items():
        if type(v) == str:
            print("{0}{1}{2}".format(
                v + " " if with_hash  else "",
                prefix + "/" if prefix else "",
                k))
        else:
            showRefs(repo, v, with_hash = with_hash , prefix="{0}{1}{2}".format(prefix, "/" if prefix else "", k))

def cmd_tag(args):
    repo  = repoFind()

    if args.name:
        createTag(repo,
                  args.name,
                  args.object,
                  type="object" if args.createTagObject else "ref")
    else:
        refs = refsList(repo)
        showRefs(repo, refs["tags"], with_hash=False)

def createTag(repo,name, ref, createTagObject = False):
    # get the GitObject from the object reference

    sha = objectFind(repo,ref)

    if createTagObject:
        tag = GitTag(repo)
        tag.kvlm = collections.OrderedDict()
        tag.kvlm[b'object'] = sha.encode()
        tag.kvlm[b'type'] = b'commit'
        tag.kvlm[b'tag'] = name.encode()

        ## Give user the ability to name tags
        tag.kvlm[b'tagger'] =  b'verFlow <verFlow@example.com> '
        tag.kvlm[None] = b"A tag generated by wyag, which won't let you customize the message!"
        tag_sha = objectWrite(tag)

        createRef(repo, "tags/" + name, tag_sha)
    else:
        createRef(repo, "tags/" + name, sha)

def createRef(repo, ref_name, sha):
    with open(repoFile(repo, "refs/" + ref_name), 'w') as fp:
        fp.write(sha + "\n")

# Cmd Rev Parse

def cmd_rev_parse(args):
    """Parses a given type of object and prints hash"""
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = repoFind()
    print (objectFind(repo, args.name, fmt, follow=True))


def cmd_ls_files(args):
    """Outputs all the files present in staging area"""
    #Get Repo
    repo = repoFind()

    #Get Index File
    index = indexRead(repo)

    if args.verbose:
        print("Index file format v{}, containing {} entries.".format(index.version, len(index.entries)))

    for entry in index.entries:
        print(entry.name)
        if args.verbose:
            print("  {} with perms: {:o}".format({ 0b1000: "regular file", 
                    0b1010: "symlink", 0b1110: "git link" }[entry.mode_type],entry.mode_perms))
            print("  on blob: {}".format(entry.sha))
            print(" Created On : {}.{} , modified on : {}.{}".format(
                    datetime.fromtimestamp(entry.ctime[0])
                    , entry.ctime[1]
                    , datetime.fromtimestamp(entry.mtime[0])
                    , entry.mtime[1]))
            print("  device: {}, inode: {}".format(entry.dev, entry.ino))
            print("  user: {} ({})  group: {} ({})".format(
                    pwd.getpwuid(entry.uid).pw_name,
                    entry.uid,
                    grp.getgrgid(entry.gid).gr_name,
                    entry.gid
                ))
            print("  flags: stage={} assume_valid={}".format(
                    entry.flag_stage,
                    entry.flag_assume_valid))
            


def cmd_add(args):
    # Placeholder function
    pass

def cmd_commit(args):
    # Placeholder function
    pass


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
    elif args.command == "hash-object":
        cmd_hash_object(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "ls-tree":
        cmd_ls_tree(args)
    elif args.command == "show-ref":
        cmd_show_ref(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "rev-parse":
        cmd_rev_parse(args)
    elif args.command == "ls-files":
        cmd_ls_files(args)
    else:
        raise ValueError("Unknown command: {}".format(args.command))