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

from verFlowRepository import repoFile, repoDir
# This section will describe the uses of refs.

# they’re text files, in the .git/refs hierarchy;
# they hold the SHA-1 identifier of an object, or a reference to another reference, ultimately to a SHA-1 (no loops!)
# example ref : 6071c08bcb4757d8c89a30d9755d2466cef8c1de or ref: refs/remotes/origin/master

def refResolver(repo, ref):
    """Takes repo and reference and resolves it"""
    path = repoFile(repo,ref)

    # Sometimes, an indirect reference may be broken.  This is normal
    # in one specific case: we're looking for HEAD on a new repository
    # with no commits.  In that case, .git/HEAD points to "ref:
    # refs/heads/main", but .git/refs/heads/main doesn't exist yet
    # (since there's no commit for it to refer to).

    if not os.path.isfile(path):
        return None
    
    with open (path, 'r') as fp:
        data = fp.read()[:-1]
        # Drop final \n ^^^^^

        if data.startswith("ref: "):
            return refResolver(repo, data[5:])
        else:
            return data


def refsList(repo, path = None):
    if not path:
        path = repoDir(repo, "refs")
    # Git shows refs sorted.  To do the same, we use
    # an OrderedDict and sort the output of listdir
    ret = collections.OrderedDict()

    for f in sorted(os.listdir(path)):
        can = os.path.join(path,f)
        if os.path.isdir(can):
            ret[f] = refsList(repo, can)
        else:
            ret[f] = refResolver(repo,can)
    
    return ret
    
