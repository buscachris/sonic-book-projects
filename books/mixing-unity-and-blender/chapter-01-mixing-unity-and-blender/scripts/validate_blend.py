"""Reopen and check the saved source against its actual FBX export manifest.

From the chapter directory:
  blender --background blender/FirstRing.blend --python scripts/validate_blend.py
This reads the source and writes verification/blender-checks.json only.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import bpy
from mathutils import Vector


CHAPTER = Path(__file__).resolve().parents[1]
manifest = json.loads((CHAPTER / "unity/Assets/Art/scene-manifest.json").read_text())
scene = bpy.context.scene
art = [obj for obj in scene.objects if obj.type == "MESH" and
       all(collection.name != "Studio" for collection in obj.users_collection)]
depsgraph = bpy.context.evaluated_depsgraph_get()
corners = []
triangles = 0
invalid_materials = []
for obj in art:
    evaluated = obj.evaluated_get(depsgraph)
    corners.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    triangles += len(mesh.loop_triangles)
    if (not mesh.materials or any(material is None for material in mesh.materials) or
            any(face.material_index >= len(mesh.materials) for face in mesh.polygons)):
        invalid_materials.append(obj.name)
    evaluated.to_mesh_clear()

minimum = [min(point[axis] for point in corners) for axis in range(3)]
maximum = [max(point[axis] for point in corners) for axis in range(3)]
bounds_match = all(abs(actual - expected) < .0001
                   for actual, expected in zip(minimum + maximum,
                                               manifest["boundsMinBlender"] + manifest["boundsMaxBlender"]))
landmarks_match = all(
    (scene.objects[point["name"]].location - Vector(point["position"])).length < .0001
    for point in manifest["landmarks"])
external_images = [image.filepath for image in bpy.data.images
                   if image.source == "FILE" and not image.packed_file]
checks = {
    "meshCountMatchesExport": len(art) == manifest["meshCount"],
    "triangleCountMatchesExport": triangles == manifest["trianglesAfterModifiers"],
    "boundsMatchExport": bounds_match,
    "landmarksMatchExport": landmarks_match,
    "fiveNamedRings": len([obj for obj in art if obj.name.startswith("Ring_")]) == 5,
    "metricScale": scene.unit_settings.system == "METRIC" and scene.unit_settings.scale_length == 1,
    "cameraNearClip": scene.camera is not None and abs(scene.camera.data.clip_start - .01) < .000001,
    "allFacesHaveMaterials": not invalid_materials,
    "noExternalTextureOrLibraryDependencies": not external_images and not list(bpy.data.libraries),
    "nativeSourceWasOpened": Path(bpy.data.filepath).resolve() == (CHAPTER / "blender/FirstRing.blend").resolve(),
}
result = {
    "passed": all(checks.values()),
    "checkedAtUtc": datetime.now(timezone.utc).isoformat(),
    "blenderVersion": bpy.app.version_string,
    "source": "blender/FirstRing.blend",
    "meshCount": len(art),
    "trianglesAfterModifiers": triangles,
    "boundsMinBlender": minimum,
    "boundsMaxBlender": maximum,
    "checks": checks,
}
destination = CHAPTER / "verification/blender-checks.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2) + "\n")
print("CHAPTER_BLENDER_VERIFICATION " + json.dumps(result))
if not result["passed"]:
    raise RuntimeError("Blender verification failed: " + ", ".join(name for name, passed in checks.items() if not passed))
