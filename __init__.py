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
    "category" : "Vertex"
}

import bpy
from pprint import pprint
import bmesh
import mathutils

class VertexCopyProperties(bpy.types.Operator):
    """Copy Vertex Properties"""
    bl_idname = "vertex.copy_properties"
    bl_label = "Copy Properties"
    bl_options = {'REGISTER', 'UNDO'}

    copyTransform: bpy.props.BoolProperty(name="Transform",description="Copy the active vertex transform to children.",default=False)
    copyNormals: bpy.props.BoolProperty(name="Normals",description="Copy the normal of the vertex to children.",default=False)
    copyShapeKeys: bpy.props.BoolProperty(name="Shape Keys",description="Copy the active vertex shapekeys to children.",default=False)
    copyWeights: bpy.props.BoolProperty(name="Weights",description="Copy the active vertex weights to children.",default=False)
    

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        #note to self: A requirement of this, is that it needs to also work with multiple selected objects.
        if context.active_object is None:
            return quit_and_end_context(self,"Must have an object selected.")
        if context.active_object.mode != 'EDIT':
            return quit_and_end_context(self,"Must be in edit mode.")
        if context.active_object.type != 'MESH':
            return quit_and_end_context(self,"Object selected is not a mesh.")
        obj = context.active_object
        if obj.data is None:
            return quit_and_end_context(self,"Must have an mesh selected.")
        mesh = obj.data
        if mesh.is_editmode==False:
            return quit_and_end_context(self,"Mesh must be in edit mode.")
        bmeshData = bmesh.from_edit_mesh(mesh)
        if bmeshData is None:
            return quit_and_end_context(self,"Mesh must have vertices.")
        
        activeVert = None        
        for vert in reversed(bmeshData.select_history):
            if isinstance(vert,bmesh.types.BMVert):
                activeVert = vert
                break
        if activeVert == None:
            return quit_and_end_context(self,"No active vertex.")

        selectedVerts = []
        normals = []

        #pre manipulations
        if self.copyNormals:
            mesh.calc_normals_split()
        for vert in bmeshData.verts:
            if vert.select:
                normals.append(activeVert.normal.copy())
                if vert != activeVert:
                    selectedVerts.append(vert)
            else:
                normals.append(vert.normal.copy())
        if len(selectedVerts) < 1:
            return quit_and_end_context(self,"Must have more than 2 vertices selected (b).")

        #begin manipulations
        for vert in selectedVerts:
            if self.copyNormals:
                vert.normal = activeVert.normal.copy()
            if self.copyTransform:
                vert.co = activeVert.co
            if self.copyShapeKeys:
                print ("Copy Shape Keys")
            if self.copyWeights:
                print ("Copy weights.")

        # post manipulations:
        if self.copyNormals:
            mesh.use_auto_smooth = True
            mesh.create_normals_split()
            mesh.normals_split_custom_set_from_vertices(normals)

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
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
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