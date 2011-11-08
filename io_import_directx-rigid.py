# Blender directX importer
# version baby

# litterature explaining the parser directions :

# I don't want to load the whole file as it can be huge : go chunks
# also I want random access to 3d datas to import pieces, not always everything
# so step1 is a whole file fast parsing, retrieving tokens name and building the internal dict
# with no 3d datas inside.
# step 2 is to call any token by their names and retrieve the 3d datas thanks to a pointer stored in dicts
# between stp1 and step 2 a script ui should be provided to select, transform etc before import.
# > I need to know the pointer position of tokens but data.tell() is slow
# a += pointer computed from line length is way faster. so I need eol -> rb mode
# and readline() is ok in binary mode 'rb' with \r\n (win) \n (unix) but not \r mac..
# 2chrs for windows, 1 for mac and lunix > win eol \r\n becomes \n\n (add a line)
# mac eol \r becomes \n so win lines info are wrong
# this also allows support for wrong files format (mixed \r and \r\n)
# for now it only works for text format, but the used methods will be independant of the container type.

# main tweaks
chunksize = 1024
quickmode = False # this to only find meshes (no parenting, no other tokens than Mesh ones)
showtree = True  # display the entire token tree in the console
showtemplate = True  # display template datas found in file

# INTERNAL DX DICT
tokens = {}
templates = {}


import os
import re
import bpy
import time
import mathutils as bmat
from mathutils import Vector
from bel.io_bdata import createMeshObject as writeMesh

#############
## TEST FILES
#############
# you can select the .x file to parse here :

file = bpy.path.abspath('//testfiles/meshes0.x') #SB3
#file = bpy.path.abspath('//testfiles/blender_xport.x')
#file = bpy.path.abspath('//testfiles/blender_xport_sphere_locate369.x')
#file = bpy.path.abspath('//testfiles/wispwind_unix.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
#file = bpy.path.abspath('//testfiles/wispwind_mac.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
#file = bpy.path.abspath('//testfiles/wispwind.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)
#file = bpy.path.abspath('//testfiles/commented.x') # example from website above (with # and //)
#file = bpy.path.abspath('//testfiles/non_inline_data.x') # example from website above (with # and //)

###################
## STEP 1 FUNCTIONS
###################

## HEADER
# returns header values or False if directx reco tag is missing
# assuming there's never comment header and that xof if the 1st
# string of the file
'''
 they look like xof 0303txt 0032
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
def dXheader(data) :
    l = data.read(4)
    if l != b'xof ' :
        print ('no header found !')
        data.seek(0)
        return False
    minor = data.read(2).decode()
    major = data.read(2).decode()
    format = data.read(4).decode().strip()
    accuracy = int(data.read(4).decode())
    data.seek(0)
    return [minor, major, format, accuracy]
    

##
def dXtree(data,quickmode = False) :
    tokens = {}
    templates = {}
    c = 0
    lvl = 0
    tree = ['']
    ptr = 0
    eol = 0
    trunkated = False
    while True :
    #for l in data.readlines() :
        lines, trunkated = nextFileChunk(trunkated)
        if lines == None : break
        for l in lines :
            ptr += eol
            c += 1
            eol = len(l) + 1
            #print(c,data.tell(),ptr+eol)
            #if l != '' : print('***',l)
            #if l == ''  : break
            l = l.strip()
            # remove blank and comment lines
            if l == '' or re.match(r_ignore,l) :
                #print('comment line %s'%l)
                continue
            #print('%s lines in %.2f\''%(c,time.clock()-t),end='\r')
            #print(c,len(l)+1,ptr,data.tell())
            if '{' in l : lvl += 1
            if '}' in l : lvl -= 1
            #print(c,lvl,tree)
            
            if quickmode == False :
                ## check for templates
                if re.match(r_template,l) :
                    tname = l.split(' ')[1]
                    templates[tname] = {'pointer' : ptr, 'line' : c}
                    continue

                ## check for {references}
                if re.match(r_refsectionname,l) :
                    refname = l[1:-1].strip()
                    print('FOUND reference to %s in %s at line %s'%(refname,tree[lvl],c))
                    #tree = tree[0:lvl]
                    parent = tree[lvl]
                    # tag it as a reference, since it's not exactly a child.
                    # put it in there since order can matter in sub tokens declaration
                    tokens[parent]['childs'].append('*'+refname) 
                    if refname not in tokens :
                        print('reference to %s done before its declaration (line %s)\ncreated dummy'%(refname,c))
                        tokens[refname] = {}
                    if 'user' not in tokens[refname] : tokens[refname]['users'] = [parent]
                    else : tokens[refname]['users'].append(parent)
                    continue

            ## check for anyhting { or Mesh in quickmode
            if re.match(r_sectionname,l) :
                mesh = getFramename(l,tokens)
                #print('FOUND %s %s %s %s'%(mesh,c,lvl,tree))
                #print('pointer %s %s'%(data.tell(),ptr))
                typ = l.split(' ')[0].strip()
                tree = tree[0:lvl]
                parent = tree[-1]
                if mesh in tokens :
                    tokens[mesh]['pointer'] = ptr
                    tokens[mesh]['line'] = c
                    tokens[mesh]['parent'] = parent
                    tokens[mesh]['childs'] = []
                    tokens[mesh]['type'] = typ
                    
                else : tokens[mesh] = {'pointer': ptr, 'line' : c, 'parent':parent, 'childs':[], 'users':[], 'type':typ}
                tree.append(mesh)
                if lvl > 1 and quickmode == False :
                    tokens[parent]['childs'].append(mesh)

    return tokens, templates
                
## returns file binary chunks
def nextFileChunk(trunkated=False,chunksize=1024) :
    chunk = data.read(chunksize)
    lines = chunk.decode()
    #if stream : return lines.replace('\r','').replace('\n','')
    lines = lines.replace('\r','\n').split('\n')
    if trunkated : lines[0] = trunkated + lines[0]
    if len(lines) == 1 : 
        if lines[0] == '' : return None, None
        return lines, False
    return lines, lines.pop()


# rename token with noname or too short names
def getFramename(l,tokens) :
    name = l.split(' ')[1].strip()
    if name and name[-1] == '{' : name = name[:-1]
    if len(name) < 3 :
        nam = l.split(' ')[0].strip()
        id = 0
        name = nam #'%s%.5d'%(nam,id)
        while name in tokens :
            id += 1
            name = '%s%.5d'%(nam,id)
    # case exists ?
    if name in tokens :
        print('duplicate name ! %s (does nothing)'%name)
    return name


## populate a template with its datas
# this make them available in the internal dict. sould be use in step 2 for unknown data type at least
def readTemplate(tpl_name,display=False) :
    ptr = templates[tpl_name]['pointer']
    line = templates[tpl_name]['line']
    #print('> %s at line %s (chr %s)'%(tpl_name,line,ptr))
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
            templates[tpl_name]['restriction'] = member
            continue  
        templates[tpl_name]['members'].append( member.split(' ') )

    if display : 
        print('\ntemplate %s :'%tpl_name)
        for k,v in templates[tpl_name].items() :
            if k != 'members' :
                print('  %s : %s'%(k,v))
            else :
                for member in v :
                    print('  %s'%str(member)[1:-1].replace(',',' ').replace("'",''))
            
        if tpl_name in defaultTemplates :
            defaultTemplates[tpl_name]['line'] = templates[tpl_name]['line']
            defaultTemplates[tpl_name]['pointer'] = templates[tpl_name]['pointer']
            if defaultTemplates[tpl_name] != templates[tpl_name] :
                print('! DIFFERS FROM BUILTIN TEMPLATE :')
                print('default template %s :'%tpl_name)
                for k,v in defaultTemplates[tpl_name].items() :
                    if k != 'members' :
                        print('  %s : %s'%(k,v))
                    else :
                        for member in v :
                            print('  %s'%str(member)[1:-1].replace(',',' ').replace("'",''))
            else :
                print('MATCHES BUILTIN TEMPLATE')

        
###################
## STEP 2 FUNCTIONS
###################
# once the internal dict is populated the functions below can be used

## from a list of tokens, displays every child, users and references
'''
  walk_dxtree( [ 'Mesh01', 'Mesh02' ] ) # for particular pieces
  walk_dxtree(tokens.keys()) for the whole tree
'''
def walk_dXtree(field,lvl=0,tab='') :
    for fi, framename in enumerate(field) :
        if lvl > 0 or tokens[framename]['parent'] == '' :
            if framename not in tokens :
                framename = framename[1:]
                ref = 'ref: '
            else : ref = False
            
            frame_type = tokens[framename]['type']
            line = ('{:7}'.format(tokens[framename]['line']))
            log = ' %s%s (%s)'%( ref if ref else '', framename, frame_type )
            print('%s.%s%s'%(line, tab, log))
            if fi == len(field) - 1 : tab = tab[:-3] + '   '

            if ref == False :
                for user in tokens[framename]['users'] :
                     print('%s.%s |__ user: %s'%(line, tab.replace('_',' '), user))
                walk_dXtree(tokens[framename]['childs'],lvl+1,tab.replace('_',' ')+' |__')
            
            if fi == len(field) - 1 and len(tokens[framename]['childs']) == 0 :
                print('%s.%s'%(line,tab))

    
## converts directX 3dvectors to blender 3d vectors
def Vector3d(string) :
    co = string.split(';')
    return Vector((float(co[0]), float(co[1]), float(co[2])))

## remove eol, comments, spaces from a raw block of datas
def cleanBlock(block) :
    while '//' in block :
        s = block.index('//')
        e = block.index('\n',s+1)
        block = block[0:s] + block[e:]
    while '#' in block :
        s = block.index('#')
        e = block.index('\n',s+1)
        block = block[0:s] + block[e:]
    block = block.replace('\n','').replace(' ','').replace('\t ','')
    return block


def dXdata(block,datatype,s=0) :
    if datatype == 'DWORD' :
        e = block.index(';',s+1)
        return int(block[s:e]), e+1
    elif datatype == 'Vector' : # only as area member
        co = block.split(';')
        return Vector((float(co[0]), float(co[1]), float(co[2]))), s + len(block)

    
def DWORD(block,s=0) :
    return dXdata(block,'DWORD',s)
    #e = block.index(';',s+1)
    #return int(block[s:e]), e+1
    
    
def dXarray(block,length,datatype,s=0) :
    lst = []
    lookup = []
    eoi = ';,'
    for i in range(length) :
        if i+1 == length : eoi = ';;'
        e = block.index(eoi,s)
        dta, na = dXdata(block[s:e+1],datatype)
        if dta in lst :
            vi = lst.index(dta)
        else :
            lst.append( dta )
            vi = len(lst) - 1
        lookup.append(vi)
        s = e + 2
    return lst, s, lookup

##
def readMesh(block) :
    verts = []
    faces = []
    # verts
    vlookup = []
    nVerts, s = DWORD(block)
    #print('%s verts'%nVerts)
    #eoi = ';,'
    #s = e + 1
    verts, s, lookup = dXarray(block,nVerts,'Vector',s)
    '''
    for i in range(nVerts) :
        if i+1 == nVerts : eoi = ';;'
        e = block.index(eoi,s)
        vert = Vector3d( block[s:e] )
        #print(i,vert)
        if vert in verts :
            vi = verts.index(vert)
        else :
            verts.append( vert )
            vi = len(verts) - 1
        vlookup.append(vi)
        s = e + 2
    '''
    # faces
    nFaces, s = DWORD(block,s)
    #print('%s faces'%nFaces)
    eoi = ';,'
    for i in range(nFaces) :
        if i+1 == nFaces : eoi = ';;'
        e = block.index(';',s)
        #print(block[s:e])
        ftyp = int( block[s:e] ) # tris or quads
        s = e + 1
        e = block.index(eoi,s)
        # patch for at least dx blender x export
        # when fields are not as x3 or x4 array member like 3;v0,v1,v2;,
        # but as a seq of floats like 3;v0;v1;v2;,
        tupleface = block[s:e]
        if ',' not in tupleface : tupleface = tupleface.replace(';',',')
        tupleface = eval(tupleface)
        #faces.append( tupleface )

        face = []
        for f in tupleface :
            face.append(lookup[f])
        faces.append( face )

        s = e + 2
    return verts, faces, lookup
       

##  read any kind of token data block
# by default the block is cleaned from inline comment space etc to allow data parsing
# cleaned = False (retrieve all bytes) is used if one needs to compute a file byte pointer
# to mimic the file.tell() function and use it with file.seek()
def readBlock(frame, clean=True) :
    ptr = frame['pointer']
    data.seek(ptr)
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
    s = block.index('{') + 1
    e = block.index('}')
    block = block[s:e]
    if clean : block = cleanBlock(block)
    return block

def readToken(tokenname) :
    token = tokens[tokenname]
    typ = token['typ']
    if typ in templates : tpl = templates[typ]
    elif typ in defaultTemplates : tpl = defaultTemplates[typ]
    else :
        print("can't find any template to read %s (type : %s)"%(tokenname,typ))
        return False
    for member in tpl['members'] :
        mbrtyp = member[0]
        mbrname = member[-1]
        if mbrtyp ==  'array' :
            ambrtyp = member[1]
            s = mbrname.index('[')
            e = mbrname.index(']')
            print(mbrname[s:e])
            length = eval(mbrname[s:e])
        else :
            length = 1
        
        exec('%s = %s'%(mbrname,mbrvalue))

###################################################
defaultTemplates={}
# mesh template
defaultTemplates['Mesh'] = {
    'uuid' : '<3d82ab44-62da-11cf-ab39-0020af71e433>',
    'restriction' : '[...]',
    'members' : [
        ['DWORD', 'nVertices'],
        ['array', 'Vector', 'vertices[nVertices]'],
        ['DWORD', 'nFaces'],
        ['array', 'MeshFace', 'faces[nFaces]'],
    ]
}

defaultTemplates['FrameTransformMatrix'] = {
    'uuid' : '<f6f23f41-7686-11cf-8f52-0040333594a3>',
    'restriction' : 'closed',
    'members' : [
        ['Matrix4x4', 'frameMatrix']
    ]
}

tpl_member_type = [
    'WORD',
    'DWORD',
    'FLOAT',
    'DOUBLE',
    'CHAR',
    'UCHAR',
    'BYTE',
    'STRING',
    'array',
    'Matrix4x4',
    'Vector',
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
'''

# COMMON REGEX
space = '[\ \t]{1,}' # at least one space / tab
space0 = '[\ \t]{0,}' # zero or more space / tab

# DIRECTX REGEX TOKENS
r_template = r'template' + space + '[\w]*' + space0 + '\{'
if quickmode :
    r_sectionname = r'Mesh' + space + '[\W-]*'
else :
    r_sectionname = r'[\w]*' + space + '[\w-]*' + space0 + '\{'
r_refsectionname = r'\{' + space0 + '[\w-]*' + space0 + '\}'
r_endsection = r'\{|\}'

# dX comments
r_ignore = r'#|//'

#r_frame = r'Frame' + space + '[\w]*'
#r_matrix = r'FrameTransformMatrix' + space + '\{[\s\d.,-]*'
#r_mesh = r'Mesh' + space + '[\W]*'

###################################################


print('\nDirectXimporter :')

data = open(file,'rb')
header = dXheader(data)

if header :
    minor, major, format, accuracy = header
    print('%s directX header'%os.path.basename(file))
    print('  minor  : %s'%(minor))
    print('  major  : %s'%(major))
    print('  format : %s'%(format))
    print('  floats are %s bits'%(accuracy))

    if format == 'txt' :

        ## FILE READ : STEP 1 : STRUCTURE
        print('\nBuilding internal .x tree')
        t = time.clock()
        tokens, templates = dXtree(data,quickmode)
        readstruct_time = time.clock()-t
        print('builded tree in %.2f\''%(readstruct_time)) # ,end='\r')

        ## populate templates with datas  works but tpl ar not used for now )
        ##  works but tpl ar not used for now
        for tplname in templates :
            readTemplate(tplname,showtemplate)

        ## DATA TREE CHECK
        if showtree :
            print('\nDirectX Data Tree :\n')
            walk_dXtree(tokens.keys())
        
        ## DATA IMPORTATION
        print('\nImporting every MESH : \n')
        for framename,frame in tokens.items() :
            if frame['type'] == 'Mesh' :
                verts = []
                edges = []
                faces = []
                matslots = []
                mats = []
                uvs = []
                datablock = readBlock(frame)
                verts, faces, vlookup = readMesh(datablock)
                '''
                for childname in frame['type']['childs'] :
                    if childname[0] == '*' : childname = childname[1:]
                    tokens[childname]['type'] == 'MeshTextureCoords' :
                        datablock = readBlock(tokens[childname])
                        uv = readUV(datablock)
                        uvs.append(uv)
                '''
    
                writeMesh(framename, False, verts, edges, faces, matslots, mats, uvs)
                
    else :
        print('only .x files in text format are currently supported')
        print('please share your file to make the importer evolve')
        
        