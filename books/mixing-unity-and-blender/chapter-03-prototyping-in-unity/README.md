# Chapter 3 — Prototyping in Unity

This chapter is the starting point for a Sonic-inspired level blockout. The current project sets up the editor and its modeling tools. Geometry and a playable scene are still pending.

## Open the project

Open the `unity` directory in Unity Hub with editor 6000.3.4f1. Unity restores ProBuilder 6.0.9 for blocking out geometry and Universal Render Pipeline 17.3.0 for rendering. Keeping the package manifest and lock together makes the editor setup reproducible.

The original editor script at [Bootstrap.cs](unity/Assets/Editor/Bootstrap.cs) logs the Unity version. From this chapter directory, use the Unity editor executable for your installation:

```sh
Unity -batchmode -quit -projectPath "$PWD/unity" -executeMethod SonicBook.Chapter03.Bootstrap.Check -logFile -
```

Look for `GHZ_PACKAGE_SETUP` followed by the editor version. The manifest and lockfile were parsed and their ProBuilder and URP versions matched. Editor execution and gameplay are unverified for this snapshot.
