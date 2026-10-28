"""Build an original Sonic-inspired Chapter 1 diorama in Blender.

Run from any directory:
  blender --background --factory-startup --python path/to/build_scene.py
Append `-- --render` to also produce the Blender preview.

This is deliberately primitive modelling: cubes, tori, cylinders, and a few
small explicit meshes. No downloaded models, textures, or Blender add-ons.
"""

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


CHAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_scene import export_art

ART = CHAPTER / "unity" / "Assets" / "Art"
BLEND = CHAPTER / "blender" / "FirstRing.blend"
PALETTE = {
    "Grass": ("62C52C", 0.0, 0.76),
    "GrassLight": ("92DF36", 0.0, 0.70),
    "GrassDark": ("268C44", 0.0, 0.83),
    "Soil": ("93451F", 0.0, 0.90),
    "SoilLight": ("C77334", 0.0, 0.85),
    "Sand": ("F4C87C", 0.0, 0.82),
    "Gold": ("FFBE26", 0.65, 0.25),
    "Trunk": ("AE6439", 0.0, 0.85),
    "TrunkLight": ("D49553", 0.0, 0.80),
    "Leaf": ("218E57", 0.0, 0.78),
    "LeafLight": ("61C447", 0.0, 0.72),
    "Ocean": ("20A6BA", 0.12, 0.30),
    "Foam": ("A9F3E5", 0.0, 0.45),
    "Plinth": ("12495B", 0.10, 0.65),
    "Blue": ("1859D4", 0.05, 0.46),
    "Red": ("EB5148", 0.05, 0.45),
    "White": ("FFF3D5", 0.0, 0.65),
    "FlowerCenter": ("54372C", 0.0, 0.90),
    "Petal": ("FFD452", 0.0, 0.65),
    "Backdrop": ("102D42", 0.0, 0.90),
}
MATERIALS = {}
COLLECTIONS = {}


def linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def make_materials():
    for name, (color, metal, roughness) in PALETTE.items():
        rgb = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = tuple(linear(v) for v in rgb) + (1,)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = mat.diffuse_color
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = roughness
        MATERIALS[name] = mat


def finish(obj, name, material, collection="Island"):
    obj.name = name
    if material:
        obj.data.materials.append(MATERIALS[material])
    if collection not in COLLECTIONS:
        target = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(target)
        COLLECTIONS[collection] = target
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    COLLECTIONS[collection].objects.link(obj)
    return obj


def cube(name, location, scale, material, bevel=0.0, collection="Island"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = finish(bpy.context.object, name, material, collection)
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Soft toy edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod = obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, location, radius, depth, material, vertices=32, collection="Island"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                      depth=depth, location=location)
    return finish(bpy.context.object, name, material, collection)


def torus(name, location, major, minor, material, rotation=(0, 0, 0), collection="Details"):
    bpy.ops.mesh.primitive_torus_add(major_segments=48, minor_segments=10,
                                    location=location, rotation=rotation,
                                    major_radius=major, minor_radius=minor)
    obj = finish(bpy.context.object, name, material, collection)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def ico(name, location, scale, material, collection="Details", subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=location)
    obj = finish(bpy.context.object, name, material, collection)
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def beam(name, start, end, radius, material, vertices=10, collection="Details"):
    delta = Vector(end) - Vector(start)
    obj = cylinder(name, (Vector(start) + Vector(end)) * 0.5,
                   radius, delta.length, material, vertices, collection)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def mesh(name, vertices, faces, materials, indices, collection="Island"):
    data = bpy.data.meshes.new(name + "Mesh")
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    finish(obj, name, None, collection)
    for material in materials:
        data.materials.append(MATERIALS[material])
    for face, index in zip(data.polygons, indices):
        face.material_index = index
    return obj


def checker_cliff():
    # Only external faces are needed. Each square is a material slot, so the
    # checker pattern survives export without a Blender procedural shader.
    verts, faces, indices = [], [], []

    def quad(points, index):
        first = len(verts)
        verts.extend(points)
        faces.append(tuple(range(first, first + 4)))
        indices.append(index)

    size = 0.75
    bottom = 0.45
    for i in range(12):
        x = -4.5 + i * size
        for j in range(3):
            z = bottom + j * size
            quad([(x, -3, z), (x + size, -3, z),
                  (x + size, -3, z + size), (x, -3, z + size)], (i + j) % 2)
            quad([(x + size, 3, z), (x, 3, z),
                  (x, 3, z + size), (x + size, 3, z + size)], (i + j) % 2)
    for i in range(8):
        y = -3 + i * size
        for j in range(3):
            z = bottom + j * size
            quad([(4.5, y, z), (4.5, y + size, z),
                  (4.5, y + size, z + size), (4.5, y, z + size)], (i + j) % 2)
            quad([(-4.5, y + size, z), (-4.5, y, z),
                  (-4.5, y, z + size), (-4.5, y + size, z + size)], (i + j) % 2)
    quad([(-4.5, -3, bottom), (-4.5, 3, bottom),
          (4.5, 3, bottom), (4.5, -3, bottom)], 0)
    quad([(-4.5, -3, 2.7), (4.5, -3, 2.7), (4.5, 3, 2.7), (-4.5, 3, 2.7)], 0)
    mesh("CheckerCliff", verts, faces, ["Soil", "SoilLight"], indices)
    cube("GrassCap", (0, 0, 2.78), (9.12, 6.12, 0.24), "Grass", 0.10)
    cube("GrassUndercut", (0, 0, 2.66), (9.04, 6.04, 0.12), "GrassDark", 0.04)
    for i in range(16):
        # Little triangles make the grass silhouette read from the camera.
        x = -4.3 + i * 0.56
        mesh("GrassFringe_%02d" % i,
             [(x - .20, -3.065, 2.80), (x + .20, -3.065, 2.80),
              (x + .03, -3.065, 2.48)], [(0, 2, 1)], ["Grass"], [0])


def loop_arch():
    verts, faces, indices = [], [], []
    segments = 64
    # Four vertices per section: front inner/outer and back inner/outer.
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        for y, radius in [(1.05, 1.48), (1.05, 1.91), (1.78, 1.48), (1.78, 1.91)]:
            verts.append((-1.35 + radius * math.cos(angle), y,
                          4.48 + radius * math.sin(angle)))
    for i in range(segments):
        j = (i + 1) % segments
        a, b = i * 4, j * 4
        faces.extend([(a, a + 1, b + 1, b), (a + 2, b + 2, b + 3, a + 3),
                      (a + 1, a + 3, b + 3, b + 1), (a, b, b + 2, a + 2)])
        indices.extend([i // 4 % 2, i // 4 % 2, 2, 3])
    mesh("LoopArch", verts, faces, ["Soil", "SoilLight", "GrassLight", "Sand"], indices)
    torus("LoopFrontTrim", (-1.35, 1.02, 4.48), 1.91, .045,
          "GrassLight", (math.pi / 2, 0, 0))


def palm(name, x, y, height, phase=0):
    base = Vector((x, y, 2.9))
    top = base + Vector((.30, .08, height))
    for i in range(7):
        a = base.lerp(top, i / 7)
        b = base.lerp(top, (i + 1) / 7)
        beam(name + "Trunk%02d" % i, a, b, .17 - i * .008,
             "TrunkLight" if i % 2 else "Trunk", 10, "Palms")
    ico(name + "Crown", top, (.25, .25, .24), "Leaf", "Palms")
    for i in range(7):
        angle = i * math.tau / 7 + phase
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        side = Vector((-direction.y, direction.x, 0))
        p0 = top
        p1 = top + direction * .72 + Vector((0, 0, .40))
        p2 = top + direction * 1.45 + Vector((0, 0, .12))
        p3 = top + direction * 1.92 + Vector((0, 0, -.40))
        vs = [p0, p1 + side * .36, p2 + side * .25, p3,
              p2 - side * .25, p1 - side * .36, p1 + Vector((0, 0, .10)),
              p2 + Vector((0, 0, .10))]
        fs = [(0, 1, 6), (1, 2, 7, 6), (2, 3, 7),
              (3, 4, 7), (4, 5, 6, 7), (5, 0, 6)]
        obj = mesh(name + "Frond%02d" % i, vs, fs, ["Leaf", "LeafLight"],
                   [1, 1, 1, 0, 0, 0], "Palms")
        solid = obj.modifiers.new("Leaf thickness", "SOLIDIFY")
        solid.thickness = .025
    for i, dx in enumerate([-.19, .12]):
        ico(name + "Coconut%d" % i, top + Vector((dx, -.13, -.16)),
            (.15, .15, .19), "Trunk", "Palms", 2)


def flower(name, x, y, height):
    z = 2.9 + height
    beam(name + "Stem", (x, y, 2.86), (x, y, z), .035, "GrassDark")
    for i in range(8):
        a = i * math.tau / 8
        obj = ico(name + "Petal%02d" % i,
                  (x + math.sin(a) * .22, y - .04, z + math.cos(a) * .22),
                  (.105, .06, .20), "Petal", subdivisions=2)
        obj.rotation_euler.y = a
    ico(name + "Center", (x, y - .10, z), (.17, .075, .17),
        "FlowerCenter", subdivisions=2)
    ico(name + "Leaf", (x + .11, y, z - .45), (.21, .055, .08), "LeafLight")


def text_mesh(name, body, location, size, material, collection="Sign"):
    data = bpy.data.curves.new(name, "FONT")
    data.body = body
    data.size = size
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.extrude = .004
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.pi / 2, 0, 0)
    finish(obj, name, material, collection)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def scene_geometry():
    cylinder("OceanBase", (0, 0, -.12), 7.05, .36, "Plinth", 96, "Ocean")
    cylinder("OceanSurface", (0, 0, .09), 7.0, .10, "Ocean", 96, "Ocean")
    torus("OceanRim", (0, 0, .15), 6.94, .045, "Foam", collection="Ocean")
    checker_cliff()
    loop_arch()
    palm("EastPalm", 3.18, 1.30, 3.1, .25)
    palm("WestPalm", -3.62, 1.95, 2.2, -.3)

    for i in range(5):
        x = -2.8 + i * 1.25
        z = 3.72 + .36 * math.sin(i / 4 * math.pi)
        ring = torus("Ring_%02d" % (i + 1), (x, -1.02, z), .38, .085,
                     "Gold", (math.pi / 2, 0, 0), "Rings")
        ring["lesson"] = "An editable torus; decorative in Chapter 1."
        cube("PathStone_%02d" % (i + 1), (x, -1.02, 2.925),
             (.96, .82, .055), "Sand", .07, "Path")

    # A red spring-shaped prop suggests a route without adding gameplay.
    cube("SpringBase", (3.5, -1.65, 3.0), (.90, .90, .18), "Blue", .08, "Details")
    for i in range(3):
        torus("SpringCoil_%d" % i, (3.5, -1.65, 3.17 + .13 * i),
              .22, .035, "White")
    cube("SpringTop", (3.5, -1.65, 3.55), (.84, .84, .20), "Red", .09)
    cube("SpringStripe", (3.5, -1.65, 3.655), (.15, .68, .012), "White", .01)

    flower("SunflowerA", -3.7, -.95, 1.05)
    flower("SunflowerB", 3.4, .10, .85)
    flower("SunflowerC", -2.75, 2.10, .65)
    for i, (x, y, s) in enumerate([(-3.5, -.1, .38), (2.9, 2.4, .45),
                                   (-2.6, -2.15, .30), (1.6, 2.5, .30),
                                   (2.6, -2.15, .23), (-4.0, 2.6, .28)]):
        ico("Bush_%02d" % i, (x, y, 2.94), (s, s * .8, s * .65),
            "GrassLight", subdivisions=2)

    for i, (x, y, z, scale) in enumerate([(-5.1, 1.2, .30, .44),
                                         (4.8, -3.2, .25, .37),
                                         (-3.5, -3.8, .27, .50)]):
        ico("ShoreRock_%02d" % i, (x, y, z), (scale, scale * .80, scale * .68), "Sand")
        obj = torus("ShoreRipple_%02d" % i, (x, y, .16), scale + .28,
                    .025, "Foam", collection="Ocean")
        obj.scale.y = .75

    cube("ChapterPlaque", (0, -3.12, 1.32), (3.60, .16, .91), "Plinth", .09, "Sign")
    text_mesh("PlaqueTitle", "FIRST RING", (0, -3.215, 1.45), .40, "White")
    text_mesh("PlaqueSubtitle", "01  /  EMERALD CIRCUIT", (0, -3.215, 1.10), .145, "Foam")
    for x in (-1.63, 1.63):
        ico("PlaqueStud" + ("L" if x < 0 else "R"), (x, -3.225, 1.33),
            (.045, .025, .045), "Gold", "Sign", 2)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def presentation():
    cube("StudioFloor", (0, 0, -.39), (200, 200, .12), "Backdrop", collection="Studio")
    bpy.ops.object.camera_add(location=(12.5, -18, 12.8))
    camera = finish(bpy.context.object, "ChapterCamera", None, "Studio")
    aim(camera, (0, 0, 2.5))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 18.7
    camera.data.clip_start = .01
    camera.data.clip_end = 300
    bpy.context.scene.camera = camera
    for name, position, power, size, color in [
            ("KeySoftbox", (-5, -7, 13), 2200, 8, (1.0, .88, .71)),
            ("FillSoftbox", (7, -2, 9), 1500, 7, (.67, .84, 1.0)),
            ("RimSoftbox", (-2, 6, 11), 2400, 6, (.86, 1.0, .89))]:
        bpy.ops.object.light_add(type="AREA", location=position)
        light = finish(bpy.context.object, name, None, "Studio")
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        aim(light, (0, 0, 2))
    scene = bpy.context.scene
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.30, .43, .55, 1)
    background.inputs["Strength"].default_value = .5
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.filepath = str(CHAPTER / "previews" / "blender-preview.png")
    # Make opening the native file pleasant without changing user preferences.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.type = "MATERIAL"
                area.spaces.active.overlay.show_extras = False


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    options = parser.parse_args(args)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.users == 0 or len(collection.objects) == 0:
            bpy.data.collections.remove(collection)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    make_materials()
    scene_geometry()
    presentation()
    manifest = export_art()
    bpy.ops.object.select_all(action="DESELECT")
    bpy.data.objects["Ring_03"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Ring_03"]
    note = bpy.data.texts.new("START HERE")
    note.write("FIRST RING / EMERALD CIRCUIT\nChapter 1: Mixing Unity and Blender\n\n"
               "Original Sonic-inspired primitive modelling study.\n"
               "Read ../README.md for the lesson, choices, and rebuild steps.\n"
               "Numpad 0: camera. Home: frame all. F12: render.\n"
               "Rings, palms, cliff, and loop are editable meshes.\n"
               "No gameplay, physics, rigs, or downloaded assets in Chapter 1.\n"
               "Export only art collections; Studio is a Blender presentation rig.\n")
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
    print("CHAPTER_EXPORT " + json.dumps({"meshes": manifest["meshCount"],
                                          "blender": bpy.app.version_string}))
    if options.render:
        (CHAPTER / "previews").mkdir(exist_ok=True)
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
