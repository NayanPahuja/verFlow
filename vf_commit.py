import configparser
import os
from object import GitTree, objectWrite
from verFlowTree import GitTreeLeaf
from vf_indexFile import vfIndexEntry
def vfConfigRead():
    xdg_config_home = os.environ["XDG_CONFIG_HOME"] if "XDG_CONFIG_HOME" in os.environ else "~/.config"
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "ver_flow/config")),
        os.path.expanduser("~/.gitconfig")
    ]

    config = configparser.ConfigParser()
    config.read(configfiles)
    return config

def getUserFromConfig(config):
    if "user" in config:
        if "name" in config["user"] and "email" in config["user"]:
            return "{} <{}>".format(config["user"]["name"], config["user"]["email"])
    return None

def treeFromIndex(repo, index):
    contents = dict()
    contents[""] = list()

    # Enumerate entries, and turn them into a dictionary where keys
    # are directories, and values are lists of directory contents.

    for entry in index.entries:
        dirname = os.path.dirname(entry.name)
        # We create all dictonary entries up to root ("").  We need
        # them *all*, because even if a directory holds no files it
        # will contain at least a tree.

        key = dirname

        while key != "":
            if not key in contents:
                contents[key] = list()
            key = os.path.dirname(key)
        #simply store the entry in the list.
        contents[dirname].append(entry)

    # Get keys (= directories) and sort them by length, descending.
    # This means that we'll always encounter a given path before its
    # parent, which is all we need, since for each directory D we'll
    # need to modify its parent P to add D's tree.
    sorted_paths = sorted(contents.keys(), key = len, reverse= True)

    # This variable will store the current tree's SHA-1.  After we're
    # done iterating over our dict, it will contain the hash for the
    # root tree.
    sha = None

    for path in sorted_paths:
        tree = GitTree()

        for entry in contents[path]:
            # An entry can be a normal GitIndexEntry read from the
            # index, or a tree we've created.
            if isinstance(entry,  vfIndexEntry): # Regular entry (a file)
                # We transcode the mode: the entry stores it as integers,
                # we need an octal ASCII representation for the tree.
                leaf_mode = "{:02o}{:04o}".format(entry.mode_type, entry.mode_perms).encode("ascii")
                leaf = GitTreeLeaf(mode = leaf_mode,path= os.path.basename(entry.name),sha= entry.sha)
            else: # Tree.  We've stored it as a pair: (basename, SHA)
                leaf = GitTreeLeaf(mode = b"040000", path=entry[0], sha=entry[1])
            tree.items.append(leaf)
        # Write the new tree object to the store.
        sha = objectWrite(tree, repo)

        # Add the new tree hash to the current dictionary's parent, as
        # a pair (basename, SHA)
        parent = os.path.dirname(path)
        base = os.path.basename(path)
        contents[parent].append((base, sha))
    
    return sha