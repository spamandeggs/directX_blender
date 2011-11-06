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
def framename(l) :
    name = l.split(' ')[1].strip()
    if len(name) < 3 :
        nam = 'noname'
        id = 0
        name = '%s%.5d'%(nam,id)
        while name in token['frame'] :
            id += 1
            name = '%s%.5d'%(nam,id)
    # case exists ?
    if name in token['frame'] :
        print('duplicate name ! %s (does nothing)'%name)
    return name

    
# TEST FILES
#file = bpy.path.abspath('//meshes0.x') SB3
file = bpy.path.abspath('//wispwind.x') # from max export (http://www.xbdev.net/3dformats/x/xfileformat.php)


# DIRECTX TOKENS
r_template = r'template\ [\w]*'
r_frame = r'Frame\ [\w]*'
r_matrix = r'FrameTransformMatrix\ \{[\s\d.,-]*'
r_mesh = r'Mesh\ {1}[\W]*'
#r_ignore = r'[#/*]'

# INTERNAL DX DICT
token = {
    'template':{},
    'frame':{}
    }

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
data = open(file,'rb')
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
    # FILE READ : STRUCTURE
    print('\nREAD .x STRUCT')
    data = open(file)
    t = time.clock()
    c = 0
    lvl = 0
    tree = ['']
    ptr = 0
    eol = 0
    
    
    # assuming Frame token is used
    while data :
    #for l in data.readlines() :
        
        ptr += eol # \r\n.. todo test unix file
        l = data.readline()
        if l == ''  : break
        c += 1
        eol = len(l)+1
        #print('%s lines in %.2f\''%(c,time.clock()-t),end='\r')
        l=l.strip()
        if l == '' : continue
        #print(c,len(l)+1,ptr,data.tell())
        if '{' in l : lvl += 1
        if '}' in l : lvl -= 1
    
        #print(c,lvl,len(tree))
        if re.match(r_template,l) :
            tname = l.split(' ')[1]
            token['template'][tname] = {'pointer' : ptr, 'line' : c}
            
        elif re.match(r_frame,l) :
            frame = framename(l)
            tree = tree[0:lvl]
            parent = tree[-1]
            token['frame'][frame] = {'pointer': ptr, 'line' : c, 'parent': parent, 'childs':[], 'type':'ob/bone'}
            tree.append(frame)
            if lvl > 1 : token['frame'][parent]['childs'].append(frame)
            
        elif re.match(r_matrix,l) :
            token['frame'][frame]['matrix'] = c
    
        elif re.match(r_mesh,l) :
            mesh = framename(l)
            tree = tree[0:lvl]
            parent = tree[-1]
            mdta =  {'pointer': ptr, 'line' : c, 'parent':parent, 'childs':[], 'type':'mesh'}
            #if 'meshes' not in token['frame'][ frame] : token['frame'][frame]['meshes'] = {mesh: mdta }
            #else : token['frame'][frame]['meshes'][mesh] = mdta
            token['frame'][mesh] = mdta
            #print(mesh,token['frame'][mesh])
            if lvl > 1 :
                token['frame'][parent]['childs'].append(mesh)
                #print(parent,token['frame'][parent])
    
    
    readstruct_time = time.clock()-t
    
    ## DATA TREE CHECK
    # 
    def walk_dxtree(field,lvl,tab='') :
        for fi, framename in enumerate(field) :
            if lvl > 0 or token['frame'][framename]['parent'] == '' :
    
                log = '%s (%s)'%( framename, token['frame'][framename]['type'] )
                line = ('{:7}'.format(token['frame'][framename]['line']))
                print('%s.%s%s'%(line, tab, log))
                if fi == len(field) - 1 : tab = tab[:-3] + '   '
                
                walk_dxtree(token['frame'][framename]['childs'],lvl+1,tab.replace('_',' ')+' |__')
                
                if fi == len(field) - 1 and len(token['frame'][framename]['childs']) == 0 :
                    print('%s.%s'%(line,tab))
    
    
    print('\nTREE TEST\n')
    walk_dxtree(token['frame'].keys(),0)
    
    
    def readTemplate(tpl_name) :
        ptr = token['template'][tpl_name]['pointer']
        line = token['template'][tpl_name]['line']
        print('> %s at line %s (chr %s)'%(tpl_name,line,ptr))
        data.seek(ptr)
        block = ''
        while True :
            l = data.readline().strip()
            block += l
            if '}' in l : break
        
        uuid = re.search(r'<.+>',block).group()
        token['template'][tpl_name]['uuid'] = uuid
        token['template'][tpl_name]['members'] = []
        token['template'][tpl_name]['restriction'] = 'closed'
        
        members = re.search(r'>.+',block).group()[1:-1].split(';')
        for member in members :
            if member == '' : continue
            if member[0] == '[' :
                if member == '[...]' :
                    token['template'][tpl_name]['restriction'] = 'open'
                else :
                    token['template'][tpl_name]['restriction'] = 'closed'
                continue  
            raw = member.split(' ')
            if len(raw) == 2 :
                mbr_name = raw[-1]
                typ = raw[0]
            elif len(raw) == 3 :
                mbr_name = raw[-1]
                typ = raw[1]
            else :
                print('template unknow case ! :\n%s'%(member))
            
            
            token['template'][tpl_name]['members'].append({
                'name':mbr_name,
                'type':typ,
            })
           
        for k,v in token['template'][tpl_name].items() :
            if k != 'members' :
                print('  %s : %s'%(k,v))
            else :
                print('  %s :'%k)
                for member in v :
                    print('    %s : %s'%(member['name'],member['type']))
                print()
                
                
    print('\nTEMPLATE READ/FILL TEST\n')
    for tpl_name in token['template'] :
        readTemplate(tpl_name)
        
    print('%s lines in %.2f\''%(c,readstruct_time),end='\r')
    
    
else :
    print('only .x files in text format are currently supported')
    print('please share your file to make the importer evolve')