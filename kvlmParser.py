#kvlmParser.py

import collections



def kvlmParse(raw,start = 0, dct = None):
    #check if dct already exists
    if not dct:
        dct = collections.OrderedDict() ##Create a new dict

    # find next space and next new line
    spc = raw.find(b' ',start)
    nl = raw.find(b'\n',start)
    # Base case
    # =========
    # If newline appears first (or there's no space at all, in which
    # case find returns -1), we assume a blank line.  A blank line
    # means the remainder of the data is the message.  We store it in
    # the dictionary, with None as the key, and return.
    if (spc < 0) or (nl < spc):
        assert nl == start
        dct[None] = raw[start+1:]
        return dct
    
    # Recursive case
    # ==============
    # we read a key-value pair and recurse for the next.
    key = raw[start:spc]

    # Find the end of the value.  Continuation lines begin with a
    # space, so we loop until we find a "\n" not followed by a space.
    end = start
    while True:
        end = raw.find(b'\n', end+1)
        if raw[end+1] !=  ord(' '): break

    # Grab the value
    # Also, drop the leading space on continuation lines
    value = raw[spc+1:end].replace(b'\n ', b'\n')

    # Don't overwrite existing data contents
    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [ dct[key], value ]
    else:
        dct[key]=value

    return kvlmParse(raw, start=end+1, dct=dct)

def kvlmSerialize(kvlm):
    ret = b''
    
    #Output Fields
    for k in kvlm.keys():
        if k == None : continue

        val = kvlm[k]

        if type(val) != list:
            val = [ val ]

        for v in val:
            ret += k + b' ' + (v.replace(b'\n', b'\n')) + b'\n'
    
    ret += b'\n' + kvlm[None] + b'\n'

    return ret
