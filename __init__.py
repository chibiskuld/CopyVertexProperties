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
from bmesh.types import BMesh

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

# (
#    mesh(
#        mesh, bmesh, obj
#    ), 
#    bmesh:vert
#)
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

        if context.active_object is None:
            return quit_and_end_context(self,"Must have an object selected.")

        meshes = getMeshes(context.selected_objects, context.active_object)
        if len(meshes)<1:
            return quit_and_end_context(self,"No meshes selected.")

        activeVert = getActiveVert(meshes[0])
        if activeVert == None:
            return quit_and_end_context(self,"No active vertex.")

        selectedVerts = getSelectedVerts(meshes,activeVert)

        if len(selectedVerts) < 2:
            return quit_and_end_context(self,"Must have more than 2 vertices selected.")
        
        #pre manipulation
        if self.copyNormals:
            prepMeshes(meshes)

        #misc reusable variables.
        coWorld = activeVert[0][2].matrix_world @ activeVert[1].co
        #begin manipulations

        for vert in selectedVerts:
            if activeVert[1]!=vert[1]:
                if self.copyTransform:
                    # if they are not the same object, convert to world space, then back to local space of the verts parent object.
                    if activeVert[0][2] != vert[0][2]: 
                        #vert[1].co = vert[0][2].matrix_local @ coWorld
                        vert[1].co = vert[0][2].matrix_world.inverted() @ coWorld
                    else:
                        vert[1].co = activeVert[1].co
                if self.copyNormals:
                    vert[1].normal = activeVert[1].normal.copy()
                if self.copyShapeKeys:
                    if len(meshes)==1:
                        CopyShapeKeys(activeVert,vert)
                if self.copyWeights:
                    print ("Copy weights.")

        #post manipulation
        if self.copyNormals:
            finalizeNormals(meshes,activeVert)

        #report any issues
        msg = ""
        if self.copyShapeKeys:
            if len(meshes)!=1:
                msg+= "At the moment, you can only copy shape keys on a single object."
        if (msg!=""):
            self.report({'WARNING'}, msg)

        return {'FINISHED'}

def getMeshes(objs, activeObj):
    meshes = []
    for obj in objs:
        if obj.type != 'MESH':
            continue
        if obj.mode != 'EDIT':
            continue
        if obj.data is None:
            continue
        me = obj.data
        if me.is_editmode==False:
            continue
        bme = bmesh.from_edit_mesh(me)
        if bme is None:
            continue

        if obj==activeObj:
            meshes.insert( 0, (me, bme, obj) )
        else:
            meshes.append( (me, bme, obj) )
    return meshes

def getBMeshes(meshes):
    bmeshes = []
    for me in meshes:
        bmeshes.append(bmesh.from_edit_mesh(me))
    return bmeshes

# theres currently a bug with active vert, if I select the last vert, in the inactive object, it gets this wrong and everything goes all wonky.
def getActiveVert(me):
    activeVert = None
    for vert in reversed(me[1].select_history):
        if isinstance(vert,bmesh.types.BMVert):
            return (me, vert)        
    return None
    
def getSelectedVerts(meshes, activeVert):
    selectedVerts = []
    selectedVerts.append(activeVert)

    for me in meshes:
        for vert in me[1].verts:
            if vert.select:
                if vert != activeVert:
                    selectedVerts.append((me,vert))
    return selectedVerts


# Actual Manipulators
def prepMeshes(meshes):
    for me in meshes:
        me[0].calc_normals_split()        


def finalizeNormals(meshes, activeVert):
    for me in meshes:
        normals = []
        for vert in me[1].verts:
            if vert.select: #it probably doesn't need to do this check. normal at this point should equal active Normal.
                normals.append(activeVert[1].normal.copy())
            else:
                normals.append(vert.normal.copy())
        me[0].use_auto_smooth = True
        me[0].create_normals_split()
        me[0].normals_split_custom_set_from_vertices(normals)


def quit_and_end_context(self, msg):
    self.report({'WARNING'}, msg)
    return {'CANCELLED'}

def CopyShapeKeys( activeVert, vert ):
    vbas = ""
    abas = ""
    for key in activeVert[0][1].verts.layers.shape.keys():
        val = activeVert[0][1].verts.layers.shape.get(key)
        if vbas == "":
            vbas = vert[1][val]
        if abas == "":
            abas = activeVert[1][val]

        diff = activeVert[1][val] - abas
        # print( str(key) + ": " + str(diff) )
        vert[1][val] = vbas + diff

def menu_func(self, context):
    self.layout.operator(VertexCopyProperties.bl_idname)


# store keymaps here to access after registration
addon_keymaps = []


def register():
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