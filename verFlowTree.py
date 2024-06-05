# verFlowTree.py

class GitTreeLeaf(object):

    def __init__(self,mode,path,sha) -> None:
        self.mode = mode
        self.path = path
        self.sha = sha

def treeParseSingle(raw, start = 0):
    # Find the space terminator of the mode

    x = raw.find(b' ',start)
    assert x - start == 5 or x - start == 6

    #Read the mode

    mode = raw[start:x]
    
    if len(mode) == 5:
        mode = b" " + mode
    
    #Find the null terminator of the path
    y = raw.find(b'\00', x)

    #Read the path
    path = raw[x+1:y]

    #Read the sha-1 and convert it to a hex string

    sha = format(int.from_bytes(raw[y+1:y+21],"big"),"040x")
    return y+21, GitTreeLeaf(mode, path.decode("utf8"), sha)


def treeParser(raw):
    pos = 0
    max = len(raw)
    ret = list()

    while pos < max:
        pos, data = treeParseSingle(raw,pos)
        ret.append(data)
    
    return ret


def treeLeafSortKey(leaf):
    if leaf.mode.startswith(b"10"):
        return leaf.path
    else:
        return leaf.path + "/"
    

def treeSerialize(obj):
    obj.items.sort(key = treeLeafSortKey)
    ret = b' '

    for i in obj.items:
        ret += i.mode #mode
        ret += b' ' #space
        ret += i.path.encode("utf8") #path to utf-8
        ret += b'\x00' #null terminator
        sha = int(i.sha,16)
        ret += sha.to_bytes(20, byteorder="big")
    return ret
