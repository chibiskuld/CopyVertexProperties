# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import addon_utils

bl_info = {
    "name" : "Copy Vertex Properties",
    "author" : "Skuld",
    "description" : "Copies various properties the active vertex to selected.",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D > Vertex > Copy Vertex Properties",
    "warning" : "",
    "category" : "Generic"
}

import bpy
from pprint import pprint
import bmesh

class VertexCopyProperties(bpy.types.Operator):
    """Copy Vertex Properties"""
    bl_idname = "vertex.copy_properties"
    bl_label = "Copy Properties"
    bl_options = {'REGISTER', 'UNDO'}

    copyTransform: bpy.props.BoolProperty(name="Transform",description="Copy the active vertex transform to children.",default=True)
    copyShapeKeys: bpy.props.BoolProperty(name="Shape Keys",description="Copy the active vertex shapekeys to children.",default=True)
    copyWeights: bpy.props.BoolProperty(name="Weights",description="Copy the active vertex weights to children.",default=True)
    

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        if context.active_object is None:
            return quit_and_end_context(self,"Must have an object selected.")
            
        obj = context.active_object
        if obj.data is None:
            return quit_and_end_context(self,"Must have an mesh selected.")
        mesh = obj.data
        if mesh.mode.is_editmode==False:
            return quit_and_end_context(self,"Mesh must be in edit mode.")
        bmeshData = bmesh.from_edit_mesh(mesh)
        if bmeshData is None:
            return quit_and_end_context(self,"")
        n = 0
        activeVert = None
        selectedVerts = []
        if len(bmeshData.select_history) < 2:
            return quit_and_end_context(self,"Must have more than 2 vertices selected.")
        for vert in reversed(bmeshData.select_history):
            if isinstance(vert,bmesh.types.BMVert):
                if n == 0:
                    activeVert = vert
                if n > 0:
                    selectedVerts.append(vert)
                n=n+1
        if (n < 2):
            return quit_and_end_context(self,"Must have more than 2 vertices selected.")

        #pprint(dir(context.active_object))
        #pprint(dir(context.selected_objects[0]))

        
        # print(obj.data)

        if self.copyTransform == True:
            print ("Copy Transform")
        if self.copyShapeKeys == True:
            print ("Copy Shape Keys")
        if self.copyWeights == True:
            print ("Copy weights.")

        # obj_new = obj.copy()
        # scene.collection.objects.link(obj_new)

        # factor = i / self.total
        # obj_new.location = (obj.location * factor) + (cursor * (1.0 - factor))

        return {'FINISHED'}

def quit_and_end_context(self, msg):
    print ("No active vertex, quit.")
    self.report({'WARNING'}, msg)
    return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(VertexCopyProperties.bl_idname)

# store keymaps here to access after registration
addon_keymaps = []


def register():
    print("registered")
    bpy.utils.register_class(VertexCopyProperties)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Vertex Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(VertexCopyProperties.bl_idname, 'C', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    print("unregistered")
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(VertexCopyProperties)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)


if __name__ == "__main__":
    register()