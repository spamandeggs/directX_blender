import bpy
'''
naming_method = 0   blender default (increment name)
naming_method = 1   do nothing, abort creation and use existing
naming_method = 2   create new, rename existing, 
naming_method = 3   create new, remove existing
'''
def new(name, naming_method=0) :
    if name not in bpy.data.materials or naming_method == 0:
        return bpy.data.materials.new(name=name)
    elif naming_method == 2 :
        mat = bpy.data.materials.new(name=name)
        mat.name = name
        return mat
    #elif naming_method in [ 1, 3 ] :
    return bpy.data.materials[name]
