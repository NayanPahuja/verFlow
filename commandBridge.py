# commandBridge.py
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
from verFlowRepository import repoCreate, repoFile, repoFind, repoPath, repoDir, repoDefaultConfig
from object import objectRead, objectFind, objectWrite
from object import GitBlob, GitCommit, GitTree, GitTag
from kvlmParser import kvlmParse, kvlmSerialize
from vfRefs import refsList, refResolver
from vf_indexFile import indexRead, indexWrite
from vf_indexFile import vfIndexEntry
from vf_ignore import vfignoreRead, checkIgnore
from vf_commit import treeFromIndex, getUserFromConfig, vfConfigRead
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
    """Given an object it generates the hash of that specific object"""
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
            type = item.mode[0:2]

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
    if args.createTagObject:
        objectTag = True
    else:
        objectTag = False
    if args.name:
        createTag(repo,
                  args.name,
                  args.object,
                  objectTag)
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
            

def cmd_check_ignore(args):
    """Checks the paths to ignore"""
    #Find repo as usual
    repo = repoFind()

    #rules to check ?: ignore what file

    rules = vfignoreRead(repo)
    for path in args.path:
        if checkIgnore(rules,path):
            print(path)

def cmd_status():
    repo = repoFind()
    index = indexRead(repo)
    
    cmd_status_branch(repo)
    cmd_status_head_index(repo,index)
    print()
    cmd_status_index_worktree(repo, index)

def cmd_status_branch(repo):
    branch = getActiveBranch(repo)
    if branch:
        print("On branch {}.".format(branch))
    else:
        print("HEAD detached at {}".format (objectFind(repo, "HEAD")))

def getActiveBranch(repo):
    with open(repoFile(repo,"HEAD"),"r") as f:
        head = f.read()
    
    if head.startswith("ref: refs/heads/"):
        return(head[16:-1])
    else:
        return False
    
def treeToDict(repo, ref, prefix = ""):
    ret = dict()
    tree_sha = objectFind(repo,ref,fmt = b'tree')
    tree = objectRead(repo,tree_sha)

    for leaf in tree.items:
        full_path = os.path.join(prefix, leaf.path)
        # We read the object to extract its type (this is uselessly
        # expensive: we could just open it as a file and read the
        # first few bytes)
        is_subtree = leaf.mode.startswith(b'04')
        # Depending on the type, we either store the path (if it's a
        # blob, so a regular file), or recurse (if it's another tree,
        # so a subdir)
        if is_subtree:
            ret.update(treeToDict(repo,leaf.sha,full_path))
        else:
            ret[full_path] = leaf.sha

    return ret
# Finding changes between HEAD and index
def cmd_status_head_index(repo,index):
    """Compares head and index to print files yet to be committed """
    print("Changes yet to be committed")
    head = treeToDict(repo,"HEAD")

    for entry in index.entries:
        if entry.name  in head:
            if head[entry.name] != entry.sha:
                print("  modified:", entry.name)
            del head[entry.name] # Delete the key
        else:
            print("  added:   ", entry.name)
    # Keys still in HEAD are files that we haven't met in the index,
    # and thus have been deleted.
    for entry in head.keys():
        print("  deleted: ", entry)


# Finding changes between index and worktree
def cmd_status_index_worktree(repo,index):
    print("Changes not yet staged for commit: ")

    #files to ignore
    ignore = vfignoreRead(repo)
    gitdir_prefix = repo.gitdir + os.path.sep

    all_files = list()

    # We begin by walking the filesystem

    for (root, _, files) in os.walk(repo.worktree, True):
        if root==repo.gitdir or root.startswith(gitdir_prefix):
            continue
        
        for f in files:
            full_path = os.path.join(root,f)
            rel_path = os.path.relpath(full_path,repo.worktree)
            all_files.append(rel_path)
    
    # We now traverse the index, and compare real files with the cached
    # versions.
    for entry in index.entries:
        full_path = os.path.join(repo.worktree, entry.name)
        # That file *name* is in the index

        if not os.path.exists(full_path):
            print(" deleted : ", entry.name)
        else:
            stat = os.stat(entry.name)

            # Compare metadata

            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]

            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):

                #if times are different deeply compare
                with open(full_path, "rb") as fd:
                    new_sha = objectHash(fd,b"blob",None)
                    #compare hashes for verification
                    same = entry.sha == new_sha

                    if not same:
                        print("  modified:",entry.name)

        if entry.name in all_files:
            all_files.remove(entry.name)
    print()
    print("Untracked files:")

    for f in all_files:
        # @TODO If a full directory is untracked, we should display
        # its name without its contents.
        if not checkIgnore(ignore, f):
            print(" ", f)               

def cmd_rm(args):
    repo = repoFind()
    rm(repo, args.path)

def rm(repo, paths, delete = True, skip_missing = False):
    # Find and read the index
    index = indexRead(repo)
    worktree = repo.worktree + os.sep

    #Make Paths absolute
    abspaths = list()
    for path in paths:
        abspath = os.path.abspath(path)
        if abspath.startswith(worktree):
            abspaths.append(abspath)
        else:
            raise Exception("Cannot remove paths outside of worktree: {}".format(paths))
    
    kept_entries = list()
    remove = list()

    for e in index.entries:
        full_path = os.path.join(repo.worktree, e.name)
        
        if full_path in abspaths:
            remove.append(full_path)
            abspaths.remove(full_path)
        else:
            kept_entries.append(e)

    if len(abspaths) > 0 and not skip_missing:
        raise Exception("Cannot remove paths not in the index: {}".format(abspaths))
    if delete:
        for path in remove:
            os.unlink(path)
    
    index.entries = kept_entries
    indexWrite(repo,index)

def cmd_add(args): 
    repo = repoFind()
    vfadd(repo,args.path)

def vfadd(repo, paths, delete = True, skip_missing = False):
    rm(repo,paths, delete= False, skip_missing = True)

    worktree = repo.worktree + os.sep

  # Convert the paths to pairs: (absolute, relative_to_worktree).
  # Also delete them from the index if they're present.

    clean_paths = list()

    for path in paths:
        abspath = os.path.abspath(path)
        if not (abspath.startswith(worktree) and os.path.isfile(abspath)):
            raise Exception("Not a file, or outside the worktree: {}".format(paths))
        relpath = os.path.relpath(abspath,repo.worktree)
        clean_paths.append((abspath,  relpath))

        index = indexRead(repo)

        for (abspath,relpath) in clean_paths:
            with open(abspath,"rb") as fd:
                sha = objectHash(fd, b"blob", repo)
            stat = os.stat(abspath)

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = vfIndexEntry(ctime=(ctime_s, ctime_ns), mtime=(mtime_s, mtime_ns), dev=stat.st_dev, ino=stat.st_ino,
                                    mode_type=0b1000, mode_perms=0o644, uid=stat.st_uid, gid=stat.st_gid,
                                    fsize=stat.st_size, sha=sha, flag_assume_valid=False,
                                    flag_stage=False, name=relpath)
            index.entries.append(entry)

            # Write the index back
            indexWrite(repo, index)
def commit_create(repo,tree,parent,author,timestamp,message):
    commit = GitCommit()
    commit.kvlm[b"tree"] = tree.encode("ascii")

    if parent:
        commit.kvlm[b"parent"] = parent.encode("ascii")
    
    #Format TimeZone
    offset = int(timestamp.astimezone().utcoffset().total_seconds())
    hours = offset // 3600
    minutes = (offset % 3600) // 60

    tz = "{}{:02}{:02}".format("+" if offset > 0 else "-", hours, minutes)

    author = author + timestamp.strftime(" %s ") + tz

    commit.kvlm[b"author"] = author.encode("utf8")
    commit.kvlm[b"committer"] = author.encode("utf8")
    commit.kvlm[None] = message.encode("utf8")

    return objectWrite(commit, repo)


def cmd_commit(args):
    repo = repoFind()
    index = indexRead(repo)

    tree = treeFromIndex(repo,index)
    # Create the commit object itself

    commit = commit_create(repo,
                           tree,
                           objectFind(repo, "HEAD"),
                           getUserFromConfig(vfConfigRead()),
                           datetime.now(),
                           args.message)

    # Update HEAD so our commit is now the tip of the active branch
    active_branch = getActiveBranch(repo)
    if active_branch:   # If we're on a branch, we update refs/heads/BRANCH
        with open(repoFile(repo,os.path.join("refs/heads", active_branch)),"w") as fd:
            fd.write(commit + "\n")
    else:   # Otherwise, we update HEAD itself.
        with open(repoFile(repo, "HEAD"), "w") as fd:
            fd.write("\n")


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
    elif args.command == "show-refs":
        cmd_show_ref(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "rev-parse":
        cmd_rev_parse(args)
    elif args.command == "ls-files":
        cmd_ls_files(args)
    elif args.command == "check-ignore":
        cmd_check_ignore(args)
    elif args.command == "status":
        cmd_status()
    elif args.command == "rm":
        cmd_rm(args)
    else:
        raise ValueError("Unknown command: {}".format(args.command))