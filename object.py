# importing standard libraries
import os
import hashlib
import zlib
import re
#importing other files
from verFlowRepository import repoFile, repoDir
from kvlmParser import kvlmParse,kvlmSerialize
from verFlowTree import treeParser, treeSerialize
from vfRefs import refResolver

class VerFlowObject (object):
    
    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.init()
        
    def serialize(self,repo):
        """This method MUST be implemented by subclasses."""
        raise Exception("Unimplemented!. Must be implemented by subclasses")

    def deserialize(self, data):
        """This method MUST be implemented by subclasses."""
        raise Exception("Unimplemented!. Must be implemented by subclasses")


    def init(self):
        pass  # Default implementation

def objectRead(repo, sha):
    """Read object sha from VerFlow repository repo. Return a
    VerFlowObject whose exact type depends on the object."""

    path = repoFile(repo, "objects", sha[0:2], sha[2:])

    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        # Read object type
        x = raw.find(b' ')
        fmt = raw[0:x]

        # Read and Validate object size
        y = raw.find(b'\x00', x)
        size = int(raw[x:y].decode("ascii"))

        # Validate size
        if size != len(raw) - y - 1:
            raise Exception("Malformed object {0}: bad length".format(sha))

        # Object type to class mapping
        match fmt:
            case b'commit' : c=GitCommit
            case b'tree'   : c=GitTree
            case b'tag'    : c=GitTag
            case b'blob'   : c=GitBlob
            case _:
                raise Exception("Unknown type {0} for object {1}".format(fmt.decode("ascii"), sha))
        # Call constructor
        return c(raw[y + 1:])

        
def objectWrite(obj, repo=None):
    # Serialize object data
    data = obj.serialize()
    # Add header
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # Compute hash
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        # Compute path
        path=repoFile(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, 'wb') as f:
                # Compress and write
                f.write(zlib.compress(result))
    return sha


##Object Resolver

def objectResolve(repo,name):
    """Resolve name to an object hash in repo.

This function is aware of:

 - the HEAD literal
    - short and long hashes
    - tags
    - branches
    - remote branches"""
    # List of candidates that we can return
    candidates = list()
    hashRE = re.compile(r"^[0-9A-Fa-f]{4,40}$") #check the hashRE is hexadecimal only

    # Empty String?: Abort process
    if not name.strip():
        return None
    
    if name == "HEAD":
        return [ refResolver(repo, "HEAD") ]
    
    # If it's a hex string, try for a hash.
    if hashRE.match(name):
        # This may be a hash, either small or full.  4 seems to be the
        # minimal length for git to consider something a short hash.
        name = name.lower()
        prefix = name[0:2]
        path = repoDir(repo,"objects",prefix,mkdir=False)
        if path:
            rem = name[2:]
            for f in os.listdir(path):
                if f.startswith(rem):
                    # Notice a string startswith() itself, so this
                    # works for full hashes.
                    candidates.append(prefix + f)
       # Try for references.
    as_tag = refResolver(repo, "refs/tags/" + name)
    if as_tag: # Did we find a tag?
        candidates.append(as_tag)

    as_branch = refResolver(repo, "refs/heads/" + name)
    if as_branch: # Did we find a branch?
        candidates.append(as_branch)
    
    return candidates

def objectFind(repo, name, fmt=None, follow=True):
    sha = objectResolve(repo, name)

    if not sha:
        raise Exception("No such reference {0}.".format(name))
    if len(sha) > 1:
        raise Exception("Ambiguous reference {0}: Candidates are:\n - {1}.".format(name,  "\n - ".join(sha)))
    
    sha = sha[0]

    if not fmt:
        return sha
    
    while True:
        obj = objectRead(repo,sha)
        #     ^^^^^^^^^^^ < this is a bit agressive: we're reading
          # the full object just to get its type.  And we're doing
          # that in a loop, albeit normally short.  Don't expect
          # high performance here
        if obj.fmt == fmt:
            return sha
        if not follow:
            return None
        
        ## FOllow tags
        if obj.fmt == b'tag':
            sha = obj.kvlm[b'object'].decode("ascii")
        elif obj.fmt == b'commit' and fmt == b'tree':
            sha = obj.kvlm[b'tree'].decode("ascii")
        else:
            return None

class GitBlob(VerFlowObject):
    """Object of the type Blob"""
    fmt = b'blob'

    def serialize(self):
        return self.blobdata
    
    def deserialize(self, data):
        self.blobdata = data
       
class GitCommit(VerFlowObject):
    """Object of the type Commit"""
    fmt = b'commit'

    def deserialize(self, data):
        self.kvlm = kvlmParse(data)
    
    def serialize(self):
        return kvlmSerialize(self.kvlm)
    
    def init(self):
        self.kvlm = dict()

class GitTree(VerFlowObject):
    """Object of the type Tree"""
    fmt = b'tree'

    def deserialize(self, data):
       self.items = treeParser(data)

    def serialize(self,):
        return treeSerialize(self)
    
    def init(self):
        self.items = list()

class GitTag(GitCommit):
    """Object of the type Tag"""
    fmt = b'tag'
    