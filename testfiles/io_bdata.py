##\file
# raw extract quick cleaning from blended cities2.6 project. thanks to myself for cooperation, but what a messy code we have here.
import bpy
import mathutils
from mathutils import *

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

## material MUST exist before creation of material slots
## map only uvmap 0 to its image defined in mat  for now (multitex view)
def createMeshObject(name, replace=False, verts=[], edges=[], faces=[], matslots=[], mats=[], uvs=[]) :

    if replace :
        # naming consistency for mesh w/ one user
        if name in bpy.data.objects :
            mesh = bpy.data.objects[name].data
            if mesh :
                if mesh.users == 1 : mesh.name = name
            else : 
                dprint('createMeshObject : object %s found with no mesh (%s) '%(name,type(mesh)),2)
                wipeOutObject(bpy.data.objects[name])
        # update mesh/object
        if name in bpy.data.meshes :
            mesh = bpy.data.meshes[name]
            mesh.user_clear()
            wipeOutData(mesh)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    mesh.update()

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
            mesh.materials.append(mat)
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
        for fi,f in enumerate(mesh.faces) :
            f.material_index = mats[fi]

    # uvs
    if len(uvs) > 0 :
        for uvi, uvlist in enumerate(uvs) :
            uv = mesh.uv_textures.new()
            uv.name = 'UV%s'%uvi
            for uvfi, uvface in enumerate(uvlist) :
                #uv.data[uvfi].use_twoside = True # 2.60 changes mat ways
                mslotid = mesh.faces[uvfi].material_index
                #mat = mesh.materials[mslotid]
                #tex = mat.texture_slots[0].texture
                #img = tex.image
                if matimage[mslotid] :
                    img = matimage[mslotid]
                    uv.data[uvfi].image=img
                    #uv.data[uvfi].use_image = True
                uv.data[uvfi].uv1 = Vector((uvface[0],uvface[1]))
                uv.data[uvfi].uv2 = Vector((uvface[2],uvface[3]))
                uv.data[uvfi].uv3 = Vector((uvface[4],uvface[5]))
                if len(uvface) == 8 :
                    uv.data[uvfi].uv4 = Vector((uvface[6],uvface[7]))


    if name not in bpy.data.objects or replace == False :
        ob = bpy.data.objects.new(name=name, object_data=mesh)
        dprint('  create object %s'%ob.name,2)
    else :
        ob = bpy.data.objects[name]
        ob.data = mesh
        ob.parent = None
        ob.matrix_local = Matrix()
        dprint('  reuse object %s'%ob.name,2)
    if  ob.name not in bpy.context.scene.objects.keys() :
        bpy.context.scene.objects.link(ob)
    return ob


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

# face are squared or rectangular, 
# any orientation
# vert order width then height 01 and 23 = x 12 and 03 = y
# normal default when face has been built
def uvrow(vertices,faces,normals=True) :
    uvs = []
    for face in faces :
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[-1]]
        print(v0,v1)
        lx = (v1 - v0).length
        ly = (v2 - v0).length
        # init uv
        if len(uvs) == 0 :
            x = 0
            y = 0
        elif normals :
            x = uvs[-1][2]
            y = uvs[-1][3]
        else :
            x = uvs[-1][0]
            y = uvs[-1][1]
        if normals : uvs.append([x,y,x+lx,y,x+lx,y+ly,x,y+ly])
        else : uvs.append([x+lx,y,x,y,x,y+ly,x+lx,y+ly])
    return uvs

