# Sonic Book Projects

Original Sonic-inspired Blender projects, organized by book and chapter.
Each chapter turns the lesson into a small, editable project and explains
**what the chapter teaches, what we made, and why we chose our own method**.

![First Ring — Chapter 1 Blender render](books/mixing-unity-and-blender/chapter-01-mixing-unity-and-blender/previews/blender-preview.png)

## Books

| Book directory | Chapters | Start here |
| --- | --- | --- |
| [`mixing-unity-and-blender`](books/mixing-unity-and-blender/) — working name; full book title and edition pending | 01 — Mixing Unity and Blender | [First Ring / Emerald Circuit](books/mixing-unity-and-blender/chapter-01-mixing-unity-and-blender/) |

## How the collection works

```text
books/
  <book-name>/
    README.md
    chapter-01-<chapter-name>/
      README.md       # Lesson, our approach, reasons, instructions, evidence
      blender/        # Editable .blend sources
      scripts/        # Reproducible modeling/export/validation tools
      unity/          # Engine project when the lesson needs one
      previews/       # Actual renders, labeled by application
      verification/   # Recorded checks and artifact hashes
templates/
  CHAPTER_README.md
```

- Every chapter gets its own README using the [chapter template](templates/CHAPTER_README.md).
- Each chapter is self-contained. Later work leaves earlier lessons usable.
- The `.blend` files are editable source; the scripts explain and reproduce
  the construction. Generated assets and previews are included for easy review.
- Unity caches and Blender recovery copies stay out of Git. Unity `.meta`
  files, package locks, source scenes, and exports stay in Git.
- Chapters report the versions and checks actually used, including limitations.

## Open a project

Clone this repository, choose a chapter, and follow its README. Chapter 1
includes a ready-to-open Blender file and a Unity project; rebuilding is optional.
The current files are small enough for ordinary Git, with no Git LFS requirement.

## Provenance

The geometry, palette, scripts, and scenes in this collection were made for
these exercises. The repository does not include publisher chapter text,
screenshots, code bundles, or extracted game assets.

Sonic the Hedgehog belongs to SEGA. This is an unofficial educational fan
project and is not affiliated with or endorsed by SEGA or the book publisher.
