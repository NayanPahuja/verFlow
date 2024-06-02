# importing standard libraries
import os
import hashlib
import zlib
#importing other files
import verFlowRepository as vfRepo
from kvlmParser import kvlmParse,kvlmSerialize



class VerFlowObject:
    def __init__(self, repo, data=None):
        self.repo = repo
        if data is not None:
            self.deserialize(data)
        else:
            self.init()
        
    def serialize(self):
        """This method MUST be implemented by subclasses."""
        raise NotImplementedError("Must be implemented by subclass")

    def deserialize(self, data):
        """This method MUST be implemented by subclasses."""
        raise NotImplementedError("Must be implemented by subclass")

    def init(self):
        pass  # Default implementation

def objectRead(repo, sha):
    """Read object sha from VerFlow repository repo. Return a
    VerFlowObject whose exact type depends on the object."""

    path = vfRepo.repoFile(repo, "objects", sha[0:2], sha[2:])

    if not os.path.isfile(path):
        return None

    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())

        # Read object type
        x = raw.find(b' ')
        fmt = raw[0:x]

        # Read and Validate object size
        y = raw.find(b'\x00', x)
        size = int(raw[x + 1:y].decode("ascii"))

        # Validate size
        if size != len(raw) - y - 1:
            raise Exception("Malformed object {0}: bad length".format(sha))

        # Object type to class mapping
        object_types = {
            b'commit': GitCommit,
            b'tree': GitTree,
            b'tag': GitTag,
            b'blob': GitBlob,
        }

        if fmt not in object_types:
            raise Exception("Unknown type {0} for object {1}".format(fmt.decode("ascii"), sha))

        # Call constructor
        return object_types[fmt](repo, raw[y + 1:])

        
def objectWrite(obj, repo=None):
    # Serialize object data
    data = obj.serialize()
    # Add header
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # Compute hash
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        # Compute path
        path=vfRepo.repoFile(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, 'wb') as f:
                # Compress and write
                f.write(zlib.compress(result))
    return sha
def objectFind(repo, name, fmt=None, follow=True):
    return name

class GitBlob(VerFlowObject):
    fmt = b'blob'

    def serialize(self):
        return self.blobdata
    
    def deserialize(self, data):
        self.blobdata = data
       
class GitCommit(VerFlowObject):
    fmt = b'commit'

    def deserialize(self, data):
        self.kvlm = kvlmParse(data)
    
    def serialize(self):
        return kvlmSerialize(self.kvlm)
    
    def init(self):
        self.kvlm = dict()