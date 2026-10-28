"""Export the current chapter artwork, retaining manual edits to the .blend.

blender --background blender/FirstRing.blend --python scripts/export_scene.py
Studio contains Blender-only presentation objects and is excluded.
"""

import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


CHAPTER = Path(__file__).resolve().parents[1]
ART = CHAPTER / "unity" / "Assets" / "Art"


def srgb(value):
    return 12.92 * value if value <= .0031308 else 1.055 * value ** (1 / 2.4) - .055


def export_fbx(path):
    options = dict(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", use_space_transform=True,
        bake_space_transform=True, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", use_tspace=False, use_mesh_edges=False,
        add_leaf_bones=False, bake_anim=False, path_mode="AUTO")
    if "use_selection" in bpy.ops.export_scene.fbx.get_rna_type().properties:
        result = bpy.ops.export_scene.fbx(**options)
        method = "FBX operator"
    else:
        # Some distribution builds combine Blender 5.0 with Python 3.14.
        # Blender issue #152809 drops the operator's annotated properties.
        # Call the same bundled exporter backend; change no installed files.
        from bpy_extras.io_utils import axis_conversion
        from io_scene_fbx import export_fbx_bin

        class Reporter:
            def report(self, level, message):
                print("FBX", level, message)
                if "ERROR" in level:
                    raise RuntimeError(message)

        options["global_matrix"] = axis_conversion(to_forward="-Z", to_up="Y").to_4x4()
        result = export_fbx_bin.save(Reporter(), bpy.context, **options)
        method = "Bundled FBX backend (operator property compatibility fallback)"
    if result != {"FINISHED"}:
        raise RuntimeError("FBX export did not finish: " + str(result))
    return method


def export_art():
    ART.mkdir(parents=True, exist_ok=True)
    objects = sorted(
        (obj for obj in bpy.context.scene.objects
         if obj.type == "MESH" and
         all(collection.name != "Studio" for collection in obj.users_collection)),
        key=lambda obj: obj.name)
    if not objects:
        raise RuntimeError("No chapter artwork found.")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    method = export_fbx(ART / "FirstRing.fbx")

    materials = {mat.name: mat for obj in objects for mat in obj.data.materials if mat}
    palette = []
    for name, material in sorted(materials.items()):
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        rgb = bsdf.inputs["Base Color"].default_value[:3]
        color = "".join(f"{round(max(0, min(1, srgb(c))) * 255):02X}" for c in rgb)
        palette.append(dict(name=name, hex=color,
                            metallic=round(bsdf.inputs["Metallic"].default_value, 5),
                            roughness=round(bsdf.inputs["Roughness"].default_value, 5)))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners, triangle_count = [], 0
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        corners.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        triangle_count += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    manifest = {
        "scene": "First Ring / Emerald Circuit",
        "blenderVersion": bpy.app.version_string,
        "pythonVersion": sys.version.split()[0],
        "exportMethod": method,
        "unit": "metre", "metersPerUnit": 1,
        "sourceCameraClipStart": bpy.context.scene.camera.data.clip_start,
        "meshCount": len(objects), "trianglesAfterModifiers": triangle_count,
        "boundsMinBlender": [min(c[i] for c in corners) for i in range(3)],
        "boundsMaxBlender": [max(c[i] for c in corners) for i in range(3)],
        "materials": palette,
        "landmarks": [dict(name=name, position=list(bpy.data.objects[name].location))
                      for name in ["Ring_01", "Ring_05", "GrassCap", "OceanSurface"]],
    }
    (ART / "scene-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("CHAPTER_EXPORT " + json.dumps({"meshes": len(objects), "method": method}))
    return manifest


if __name__ == "__main__":
    export_art()
