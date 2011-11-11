# Blender directX importer
bl_info = {
    "name": "DirectX Importer (faces, uv from .x as text files for now)",
    "description": "early tests",
    "author": "Littleneo / Jerome Mahieux",
    "version": (0, 4),
    "blender": (2, 6, 0),
    "api": 41098,
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export",
    "dependencies": ""
}

if "bpy" in locals():
    import imp
    if "import_x" in locals():
        imp.reload(import_x)
    #if "export_x" in locals():
    #    imp.reload(export_x)


import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 ImportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )
'''
class DisplayTree(bpy.types.Operator) :
    bl_idname = 'city.selector'
    bl_label = 'preview'

    def execute(self,context) :
'''
    
    
class ImportX(bpy.types.Operator, ImportHelper):
    '''Load a Direct x File'''
    bl_idname = "import_scene.x"
    bl_label = "Import X"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".x"
    filter_glob = StringProperty(
            default="*.x",
            options={'HIDDEN'},
            )
    show_tree = BoolProperty(
            name="Show items tree",
            description="display relationships between x items in the console",
            default=False,
            )
    show_templates = BoolProperty(
            name="Show templates",
            description="display templates defined in the .x file",
            default=False,
            )
    quickmode = BoolProperty(
            name="Quick mode",
            description="only retrieve mesh basics",
            default=False,
            )
    chunksize = EnumProperty(
            name="Chunksize",
            items=(('0', "all", ""),
                   ('4096', "4KB", ""),
                   ('2048', "2KB", ""),
                   ('1024', "1KB", ""),
                   ),
            default='2048',
            description="number of bytes red in a row",
            )
    use_ngons = BoolProperty(
            name="NGons",
            description="Import faces with more then 4 verts as fgons",
            default=True,
            )
    use_edges = BoolProperty(
            name="Lines",
            description="Import lines and faces with 2 verts as edge",
            default=True,
            )
    use_smooth_groups = BoolProperty(
            name="Smooth Groups",
            description="Surround smooth groups by sharp edges",
            default=True,
            )

    use_split_objects = BoolProperty(
            name="Object",
            description="Import OBJ Objects into Blender Objects",
            default=True,
            )
    use_split_groups = BoolProperty(
            name="Group",
            description="Import OBJ Groups into Blender Objects",
            default=True,
            )

    use_groups_as_vgroups = BoolProperty(
            name="Poly Groups",
            description="Import OBJ groups as vertex groups",
            default=False,
            )

    use_image_search = BoolProperty(
            name="Image Search",
            description="Search subdirs for any assosiated images " \
                        "(Warning, may be slow)",
            default=True,
            )

    split_mode = EnumProperty(
            name="Split",
            items=(('ON', "Split", "Split geometry, omits unused verts"),
                   ('OFF', "Keep Vert Order", "Keep vertex order from file"),
                   ),
            )

    global_clamp_size = FloatProperty(
            name="Clamp Scale",
            description="Clamp the size to this maximum (Zero to Disable)",
            min=0.0, max=1000.0,
            soft_min=0.0, soft_max=1000.0,
            default=0.0,
            )

    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='-Z',
            )

    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
            )

    def execute(self, context):
        # print("Selected: " + context.active_object.name)
        from . import import_x

        if self.split_mode == 'OFF':
            self.use_split_objects = False
            self.use_split_groups = False
        else:
            self.use_groups_as_vgroups = False

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "split_mode",
                                            ))

        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        return import_x.load(self, context, **keywords)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "show_tree")
        col.prop(self, "show_templates")
        col.prop(self, "quickmode")
        col.prop(self, "chunksize")
        col.prop(self, "use_smooth_groups")
        #row = layout.row(align=True)
        #row.prop(self, "use_ngons")
        #row.prop(self, "use_edges")
        box = layout.box()
        col = box.column()
        
        '''

        box = layout.box()
        row = box.row()
        row.prop(self, "split_mode", expand=True)

        row = box.row()
        if self.split_mode == 'ON':
            row.label(text="Split by:")
            row.prop(self, "use_split_objects")
            row.prop(self, "use_split_groups")
        else:
            row.prop(self, "use_groups_as_vgroups")

        row = layout.split(percentage=0.67)
        row.prop(self, "global_clamp_size")
        layout.prop(self, "axis_forward")
        layout.prop(self, "axis_up")

        layout.prop(self, "use_image_search")
        '''

def menu_func_import(self, context):
    self.layout.operator(ImportX.bl_idname, text="DirectX (.x)")

#def menu_func_export(self, context):
#    self.layout.operator(ExportX.bl_idname, text="DirectX (.x)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    #bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    #bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()