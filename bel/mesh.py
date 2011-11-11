##\file
# raw extract quick cleaning from blended cities2.6 project. thanks to myself for cooperation, but what a messy code we have here.
import bpy
import mathutils
from mathutils import *

import bel.uv

## material MUST exist before creation of material slots
## map only uvmap 0 to its image defined in mat  for now (multitex view)
def write(name, replace=False, verts=[], edges=[], faces=[], matslots=[], mats=[], uvs=[], smooth=False) :

    if replace :
        # naming consistency for mesh w/ one user
        if name in bpy.data.objects :
            me = bpy.data.objects[name].data
            if me :
                if me.users == 1 : me.name = name
            else : 
                dprint('createMeshObject : object %s found with no mesh (%s) '%(name,type(me)),2)
                wipeOutObject(bpy.data.objects[name])
        # update mesh/object
        if name in bpy.data.meshes :
            me = bpy.data.meshes[name]
            me.user_clear()
            wipeOutData(me)

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, faces)
    me.update()

    if smooth : shadesmooth(me)
    
    # material slots
    matimage=[]
    if len(matslots) > 0 :
        for matname in matslots :
            '''
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                mat.use_fake_user = True
                warn.append('Created missing material : %s'%matname)
            else :
            '''
            mat = bpy.data.materials[matname]
            me.materials.append(mat)
            texslot_nb = len(mat.texture_slots)
            if texslot_nb :
                texslot = mat.texture_slots[0]
                if type(texslot) != type(None) :
                    tex = texslot.texture
                    if tex.type == 'IMAGE' :
                        img = tex.image
                        if type(img) != type(None) :
                            matimage.append(img)
                            continue
            matimage.append(False)

    # map a material to each face
    if len(mats) > 0 :
        for fi,f in enumerate(me.faces) :
            f.material_index = mats[fi]

    # uvs
    if len(uvs) > 0 :
        bel.uv.write(me, uvs, matimage)

    if name not in bpy.data.objects or replace == False :
        ob = bpy.data.objects.new(name=name, object_data=me)
        dprint('  create object %s'%ob.name,2)
    else :
        ob = bpy.data.objects[name]
        ob.data = me
        ob.parent = None
        ob.matrix_local = Matrix()
        dprint('  reuse object %s'%ob.name,2)
    if  ob.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(ob)
    return ob

def shadesmooth(me,lst=True) :
    if type(lst) == list :
        for fi in lst :
            me.faces[fi].use_smooth = True
    else :
        for fi,face in enumerate(me.faces) :
            face.use_smooth = True
 
def shadeflat(me,lst=True) :
    if type(lst) == list :
        for fi in lst :
            me.faces[fi].use_smooth = False
    else :
        for fi,face in enumerate(me.faces) :
            face.use_smooth = False
           
def matToString(mat) :
    #print('*** %s %s'%(mat,type(mat)))
    return str(mat).replace('\n       ','')[6:]

def stringToMat(string) :
    return Matrix(eval(string))


def objectBuild(elm, verts, edges=[], faces=[], matslots=[], mats=[], uvs=[] ) :
    #print('build element %s (%s)'%(elm,elm.className()))
    dprint('object build',2)
    city = bpy.context.scene.city
    # apply current scale
    verts = metersToBu(verts)
    
    if type(elm) != str :
        obname = elm.objectName()
        if obname == 'not built' :
            obname = elm.name
    else : obname= elm

    obnew = createMeshObject(obname, True, verts, edges, faces, matslots, mats, uvs)
    #elm.asElement().pointer = str(ob.as_pointer())
    if type(elm) != str :
        if elm.className() == 'outlines' :
            obnew.lock_scale[2] = True
            if elm.parent :
                obnew.parent = elm.Parent().object()
        else :
            #otl = elm.asOutline()
            #ob.parent = otl.object()
            objectLock(obnew,True)
        #ob.matrix_local = Matrix() # not used
        #ob.matrix_world = Matrix() # world
    return obnew

def dprint(str,l=0) :
    print(str)


def materialsCheck(bld) :
    if hasattr(bld,'materialslots') == False :
        #print(bld.__class__.__name__)
        builderclass = eval('bpy.types.%s'%(bld.__class__.__name__))
        builderclass.materialslots=[bld.className()]

    matslots = bld.materialslots
    if len(matslots) > 0 :
        for matname in matslots :
            if matname not in bpy.data.materials :
                mat = bpy.data.materials.new(name=matname)
                mat.use_fake_user = True
                if hasattr(bld,'mat_%s'%(matname)) :
                    method = 'defined by builder'
                    matdef = eval('bld.mat_%s'%(matname))
                    mat.diffuse_color = matdef['diffuse_color']
                else :
                    method = 'random'
                    mat.diffuse_color=( random.uniform(0.0,1.0),random.uniform(0.0,1.0),random.uniform(0.0,1.0))
                dprint('Created missing material %s (%s)'%(matname,method),2)


