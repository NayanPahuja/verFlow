# We’ll begin by writing a reader for rules in ignore files, gitignore_read(). 
# The syntax of those rules is quite simple: each line in an ignore file is an exclusion pattern, 
# so files that match this pattern are ignored by status, add -A and so on. There are three special cases, though:

# Lines that begin with an exclamation mark ! negate the pattern (files that match this pattern are included, 
# even they were ignored by an earlier pattern)
# Lines that begin with a dash # are comments, and are skipped.
# A backslash \ at the beginning treats ! and # as literal characters.
# First, a parser for a single pattern. This parser returns a pair: the pattern itself,
#  and a boolean to indicate if files matching the pattern should be excluded (True) or included (False). In other words, False if the pattern did start with !, True otherwise
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

from vf_indexFile import indexRead
from object import objectRead

def vfignoreParse1(raw):
    """From the provided argument raw data checks if the file should be excluded or not.
    If file begins with ! it should be included else excluded. Outputs Data + bool"""
    raw = raw.strip()

    if not raw or raw[0] == '#':
        return None
    elif raw[0] == '!':
        return (raw[1:], False)
    elif raw[0] == '\\':
        return (raw[1:], True)
    else:
        return (raw, True)
    

def vfignoreParse(lines):
    ret = list()

    for line in lines:
        parsed = vfignoreParse1(line)
        if parsed:
            ret.append(parsed)
    return ret

class vfIgnore (object):
    absolute = None
    scoped = None

    def __init__(self,absolute,scoped):
        self.absolute = absolute
        self.scoped = scoped

def vfignoreRead(repo):
    # what to return? : a vfIgnore class object with list and dict
    ret = vfIgnore(absolute=list(),scoped=dict())

    # Read local configuration in .git/info/exclude
    repo_file = os.path.join(repo.gitdir, "info/exclude")
    if os.path.exists(repo_file):
        with open(repo_file, "r") as f:
            ret.absolute.append(vfignoreParse(f.readlines()))
    
    #Global Ignore config
    if "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.expanduser("~/.config")
    global_file = os.path.join(config_home, "ver_flow/ignore")


    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            ret.absolute.append(vfignoreParse(f.readlines()))

    # .gitignore files in the index
    index = indexRead(repo)
    for entry in index.entries:
        if entry.name == ".vfignore" or entry.name.endswith("/.vfignore"):
            dir_name = os.path.dirname(entry.name)
            contents = objectRead(repo, entry.sha)
            lines = contents.blobdata.decode("utf8").splitlines()
            ret.scoped[dir_name] = vfignoreParse(lines)
    return ret


def checkIgnoreHelper(rules,path):
    """Matches a path against a set of rules, and return the result of the last matching rule. Its not a real boolean functions, since it has three possible return values: True, False but also None. It returns None if nothing matched, so that it should continue trying with more general ignore files (eg, go one directory level up)."""
    result = None

    for pattern,value in rules:
        if fnmatch(path,pattern):
            result = value
    return result


def checkIgnoreScoped(rules,path):
    parent = os.path.dirname(path)

    while True:
        if parent in rules:
            result = checkIgnoreHelper(rules[parent], path)
            if result != None:
                return result
        if parent == "":
            break
        parent = os.path.dirname(parent)
    
    return None

def checkIgnoreAbsolute(rules, path):
    parent = os.path.dirname(path)
    for ruleset in rules:
        result = checkIgnoreHelper(ruleset, path)
        if result != None:
            return result
    return False # This is a reasonable default at this point


def checkIgnore(rules, path):
    if os.path.isabs(path):
        raise Exception("This function requires path to be relative to the repository's root")

    result = checkIgnoreScoped(rules.scoped, path)
    if result != None:
        return result

    return checkIgnoreAbsolute(rules.absolute, path)