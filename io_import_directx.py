import os
import re
import bpy
import time

print('\n\n\nBEGIN\n\n\n')

tpl_member_type = [
    'WORD',
    'DWORD',
    'FLOAT',
    'DOUBLE',
    'CHAR',
    'UCHAR',
    'BYTE',
    'STRING',
    'CSTRING', 
    'UNICODE'
]
'''
WORD     16 bits
DWORD     32 bits
FLOAT     IEEE float
DOUBLE     64 bits
CHAR     8 bits
UCHAR     8 bits
BYTE     8 bits
STRING     NULL-terminated string
CSTRING     Formatted C-string (currently unsupported)
UNICODE     UNICODE string (currently unsupported)

Header

The variable length header is compulsory and must be at the beginning of the data stream. The header contains the following:
Type     Sub Type     Size     Contents     Content Meaning
Magic Number (required)         4 bytes     "xof "     
Version Number (required)     Major Number     2 bytes     03     Major version 3
    Minor Number     2 bytes     02     Minor version 2
Format Type (required)         4 bytes     "txt "     Text File
            "bin "     Binary File
            "tzip"     MSZip Compressed Text File
            "bzip"     MSZip Compressed Binary File
Float size (required)         4 bytes     0064     64-bit floats
            0032     32-bit floats
Example

xof 0302txt 0064


'''

# rename token with noname or too short names
def getFramename(l) :
    name = l.split(' ')[1].strip()
    if name and name[-1] == '{' : name = name[:-1]
    if len(name) < 3 :
        nam = l.split(' ')[0].strip()
        id = 0
        name = nam #'%s%.5d'%(nam,id)
        while name in token['frame'] :
            id += 1
            name = '%s%.5d'%(nam,id)
    # case exists ?
    if name in token['frame'] :
        print('duplicate name ! %s (does nothing)'%name)
    return name

    
# TEST FILES
#file = bpy.path.abspath('//meshes0.x') #SB3
#file = bpy.path.abspath('//wispwind_unix.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
file = bpy.path.abspath('//wispwind_mac.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
#file = bpy.path.abspath('//wispwind.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
#file = bpy.path.abspath('//commented.x') # example from website above (with # and //)
#file = bpy.path.abspath('//non_inline_data.x') # example from website above (with # and //)

# COMMON REGEX
space = '[\ \t]{1,}' # at least one space char or a tab
space0 = '[\ \t]{0,}' # at least one space char or a tab

# DIRECTX REGEX TOKENS
r_template = r'template' + space + '[\w]*' + space0 + '\{'
#r_frame = r'Frame' + space + '[\w]*'
#r_matrix = r'FrameTransformMatrix' + space + '\{[\s\d.,-]*'
#r_mesh = r'Mesh' + space + '[\W]*'
r_sectionname = r'[\w]*' + space + '[\w-]*' + space0 + '\{'
r_refsectionname = r'\{' + space0 + '[\w-]*' + space0 + '\}'
r_endsection = r'\{|\}'
r_ignore = r'#|//'

# INTERNAL DX DICT
token = {
    'template':{},
    'frame':{}
    }

templates = {}

#def readMatrix(arg) :
    
# HEADER
#xof 0303txt 0032
'''
4       Magic Number (required) "xof "
2       Minor Version 03
2       Major Version 02
4       Format Type (required) 
    "txt " Text File
    "bin " Binary File  
    "tzip" MSZip Compressed Text File
    "bzip" MSZip Compressed Binary File
4       Float Accuracy "0032" 32 bit or "0064" 64 bit
'''

# assuming there's never comment header and that xof if the 1st
# sting of the file
data = open(file,'rbU')
l = data.read(4)
if l != b'xof ' :
    print ('no header found !')
else :
    minor = data.read(2).decode()
    major = data.read(2).decode()
    format = data.read(4).decode().strip()
    accuracy = int(data.read(4).decode())
    print('%s directX header'%os.path.basename(file))
    print('  minor  : %s'%(minor))
    print('  major  : %s'%(major))
    print('  format : %s'%(format))
    print('  floats are %s bits'%(accuracy))
    
if format == 'txt' :
    # RETRIEVE CRCF
    # I don't want to load the whole file as it can be huge
    # I need to know the pointer position of tokens but data.tell() is slow
    # a += pointer computed from line length is way faster so I need eol -> rb mode
    # readline() work in binary mode 'rb' with \r\n (win) \n (unix) but not \r mac..
    
    
    
    # FILE READ : STRUCTURE
    print('\nREAD .x STRUCT')
    data.seek(0) # = open(file,'rb')
    t = time.clock()
    c = 0
    lvl = 0
    tree = ['']
    ptr = 0
    eol = 0
    
    # removed from loop (now common to all kind)
    # keep it a bit for now
    '''            
            elif re.match(r_frame,l) :
                frame = getFramename(l)
                tree = tree[0:lvl]
                parent = tree[-1]
                token['frame'][frame] = {'pointer': ptr, 'line' : c, 'parent': parent, 'childs':[], 'type':'bone'}
                tree.append(frame)
                if lvl > 1 : token['frame'][parent]['childs'].append(frame)
                
            elif re.match(r_matrix,l) :
                token['frame'][frame]['matrix'] = c
        
            elif re.match(r_mesh,l) :
                mesh = getFramename(l)
                tree = tree[0:lvl]
                parent = tree[-1]
                mdta =  {'pointer': ptr, 'line' : c, 'parent':parent, 'childs':[] , 'type':'mesh'} # no child, dummy for simpler loops. parenting always through frame ?
                #if 'meshes' not in token['frame'][ frame] : token['frame'][frame]['meshes'] = {mesh: mdta }
                #else : token['frame'][frame]['meshes'][mesh] = mdta
                token['frame'][mesh] = mdta
                tree.append(mesh)
                #print(mesh,token['frame'][mesh])
                if lvl > 1 :
                    token['frame'][parent]['childs'].append(mesh)
                    #print(parent,token['frame'][parent])
        
    '''
    chunksize=1024
    trunkated = False
    while True :
    #for l in data.readlines() :
        

        chunk = data.read(chunksize)
        #print('chunk',chunk)
        chunk = chunk.decode().replace('\r','\n')
        #print()

        #print('>>>>>>>>',chunk)

        lines = chunk.split('\n')
        if trunkated : lines[0] = trunkated + lines[0]
        print('\nlines : %s *%s* %s'%(lines,lines[0],lines[0]==''))
        #print()
        

        if len(lines) == 1 :
            if lines[0] == '' :break
            trunkated = False
        else : trunkated = lines.pop()
        
        for l in lines :
            ptr += eol # \r\n.. todo test unix file
            c += 1
            eol = len(l) + 1
            #print(c,data.tell(),ptr+eol)
            #if l != '' : print('***',l)
            #if l == ''  : break
            
            l = l.strip()
            # blank and comment lines
            if re.match(r_ignore,l) :
                #print('comment line %s'%l)
                continue
    
    
            #print('%s lines in %.2f\''%(c,time.clock()-t),end='\r')
    
            if l == '' : continue
        
            #print(c,len(l)+1,ptr,data.tell())
            if '{' in l : lvl += 1
            if '}' in l : lvl -= 1
            
            #print(c,lvl,tree)
            if re.match(r_template,l) :
                tname = l.split(' ')[1]
                templates[tname] = {'pointer' : ptr, 'line' : c}
    
            elif re.match(r_refsectionname,l) :
                refname = l[1:-1].strip()
                print('FOUND reference to %s in %s at line %s'%(refname,tree[lvl],c))
                #tree = tree[0:lvl]
                parent = tree[lvl]
                # tag it as a reference, since it's not exactly a child.
                # put it in there since order can matter in sub tokens declaration
                token['frame'][parent]['childs'].append('*'+refname) 
                if refname not in token['frame'] :
                    print('reference to %s done before its declaration (line %s)\ncreated dummy'%(refname,c))
                    token['frame'][refname] = {}
                if 'user' not in token['frame'][refname] : token['frame'][refname]['users'] = [parent]
                else : token['frame'][refname]['users'].append(parent)

            elif re.match(r_sectionname,l) :
                mesh = getFramename(l)
                #print('FOUND %s %s %s %s'%(mesh,c,lvl,tree))
                #print('pointer %s %s'%(data.tell(),ptr))
                typ = l.split(' ')[0].strip()
                tree = tree[0:lvl]
                parent = tree[-1]
                if mesh in token['frame'] :
                    token['frame'][mesh]['pointer'] = ptr
                    token['frame'][mesh]['line'] = c
                    token['frame'][mesh]['parent'] = parent
                    token['frame'][mesh]['childs'] = []
                    token['frame'][mesh]['type'] = typ
                    
                else : token['frame'][mesh] = {'pointer': ptr, 'line' : c, 'parent':parent, 'childs':[], 'users':[], 'type':typ}
                tree.append(mesh)
                if lvl > 1 :
                    token['frame'][parent]['childs'].append(mesh)
    
    readstruct_time = time.clock()-t
    
    ## DATA TREE CHECK
    # does not display user
    def walk_dxtree(field,lvl,tab='') :
        for fi, framename in enumerate(field) :
            if lvl > 0 or token['frame'][framename]['parent'] == '' :
                if framename not in token['frame'] :
                    framename = framename[1:]
                    ref = 'ref: '
                else : ref = False
                
                frame_type = token['frame'][framename]['type']
                line = ('{:7}'.format(token['frame'][framename]['line']))
                log = ' %s%s (%s)'%( ref if ref else '', framename, frame_type )
                print('%s.%s%s'%(line, tab, log))
                if fi == len(field) - 1 : tab = tab[:-3] + '   '

                if ref == False :
                    for user in token['frame'][framename]['users'] :
                         print('%s.%s |__ user: %s'%(line, tab.replace('_',' '), user))
                    walk_dxtree(token['frame'][framename]['childs'],lvl+1,tab.replace('_',' ')+' |__')
                
                if fi == len(field) - 1 and len(token['frame'][framename]['childs']) == 0 :
                    print('%s.%s'%(line,tab))
    
    
    print('\nTREE TEST\n')
    walk_dxtree(token['frame'].keys(),0)

    def readVertices(block) :
        nVerts = block[0:block.index(';')]
        print(nVerts)

    def nextFileChunk(trunkated=False,chunksize=1024) :
        chunk = data.read(chunksize)
        lines = chunk.decode()
        #if stream : return lines.replace('\r','').replace('\n','')
        lines = lines.replace('\r','\n').split('\n')
        if trunkated : lines[0] = trunkated + lines[0]
        if len(lines) == 1 and lines[0] == '' : return None, None
        return lines, lines.pop()

    def readSection(frame) :
        ptr = frame['pointer']
        data.seek(0)
        data.seek(ptr)
        #print(ptr)
        #print(data.read(20))
        #popo()
        block = ''
        #lvl = 0
        trunkated = False
        go = True
        while go :
            lines, trunkated = nextFileChunk(trunkated,chunksize)
            if lines == None : break
            for l in lines :
                #print(l)
                #eol = len(l) + 1
                l = l.strip()
                #c += 1
                block += l+'\n'
                if re.match(r_endsection,l) :
                    go = False
                    break
                    
        #print('>>',block)
        s = block.index('{') + 1
        e = block.index('}')

        return block[s:e]

    def readTemplate(tpl_name) :
        ptr = templates[tpl_name]['pointer']
        line = templates[tpl_name]['line']
        print('> %s at line %s (chr %s)'%(tpl_name,line,ptr))
        data.seek(ptr)
        block = ''
        trunkated = False
        go = True
        while go :
            lines, trunkated = nextFileChunk(trunkated,chunksize) # stream ?
            if lines == None : break
            for l in lines :
                #l = data.readline().decode().strip()
                block += l.strip()
                if '}' in l :
                    go = False
                    break
        
        uuid = re.search(r'<.+>',block).group()
        templates[tpl_name]['uuid'] = uuid
        templates[tpl_name]['members'] = []
        templates[tpl_name]['restriction'] = 'closed'
        
        members = re.search(r'>.+',block).group()[1:-1].split(';')
        for member in members :
            if member == '' : continue
            if member[0] == '[' :
                if member == '[...]' :
                    templates[tpl_name]['restriction'] = 'open'
                else :
                    templates[tpl_name]['restriction'] = 'closed'
                continue  
            raw = member.split(' ')
            #print(member)
            if len(raw) == 2 :
                mbr_name = raw[-1]
                typ = raw[0]
            elif len(raw) == 3 :
                mbr_name = raw[-1]
                typ = raw[1]
            else :
                print('template unknow case ! %s:\n%s'%(len(raw),member))
            
            
            templates[tpl_name]['members'].append({
                'name':mbr_name,
                'type':typ,
            })
           
        for k,v in templates[tpl_name].items() :
            if k != 'members' :
                print('  %s : %s'%(k,v))
            else :
                print('  %s :'%k)
                for member in v :
                    print('    %s : %s'%(member['name'],member['type']))
                print()
                
                
    print('\nTEMPLATE READ/FILL TEST\n')
    for tplname in templates :
        readTemplate(tplname)
   
    print('\nMESH verts/faces TEST\n')
    for framename,frame in token['frame'].items() :
        if frame['type'] == 'Mesh' :
            print(framename,frame['line'])
            block = readSection(frame)
            print ('>',block[0:30])
            readVertices(block)
            #print()
            #for childname in frame['childs'] :
            #    print(childname)
                
    print('%s lines in %.2f\''%(c,readstruct_time),end='\r')


    
else :
    print('only .x files in text format are currently supported')
    print('please share your file to make the importer evolve')