# Blender ↔ Unity studies

This book directory uses **`mixing-unity-and-blender` as a working name**, taken
from the supplied first chapter. The full book title and edition have not yet
been supplied; this is not a claim about the book's official title.

We follow each supplied chapter's learning objective and create an original
Sonic-inspired interpretation in Blender. Every chapter README explains the
lesson in our own words, the finished project, the chosen method, and why it
fits that lesson.

| Chapter | Project | Focus |
| --- | --- | --- |
| [01 — Mixing Unity and Blender](chapter-01-mixing-unity-and-blender/) | **First Ring / Emerald Circuit** | Editable Blender artwork, explicit FBX export, Unity URP import, scale, materials, camera clipping, and project organization |
| [03 — Prototyping in Unity](chapter-03-prototyping-in-unity/) | Unity editor bootstrap | ProBuilder and URP package setup for level blockout |

Chapter 1 introduces the tool workflow with a static diorama. It has no player
controller or collectible behavior. The Chapter 3 folder contains the editor setup for a later blockout.

## Versions

The supplied chapter recommends Blender 5.1 (or 5.2 LTS) and Unity 6.3 LTS.
Our first project was built with the installed **Blender 5.0.0** and
**Unity 6000.3.4f1**, with **URP 17.3.0**. The chapter records what was tested
and the small export workaround needed by this Linux Blender build.

## Chapter conventions

Keep each chapter's source, export, Unity project, preview, and verification
together. Preserve earlier chapters when adding a new one. Use the shared
[README template](../../templates/CHAPTER_README.md), including the
**Our approach and why** section, so the collection records our decisions as
well as the final assets.
