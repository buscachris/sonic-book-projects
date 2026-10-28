using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace SonicBook.Chapter01
{
    // Editor automation only: Chapter 1 deliberately has no gameplay code.
    public static class ChapterBuilder
    {
        const string ModelPath = "Assets/Art/FirstRing.fbx";
        const string ScenePath = "Assets/Scenes/FirstRing.unity";
        const string PrefabPath = "Assets/Art/FirstRing.prefab";
        static string Chapter => Directory.GetParent(Application.dataPath).Parent.FullName;

        [Serializable] public class Surface
        {
            public string name, hex;
            public float metallic, roughness;
        }

        [Serializable] public class Landmark
        {
            public string name;
            public float[] position;
        }

        [Serializable] public class Manifest
        {
            public string scene, blenderVersion, pythonVersion, exportMethod;
            public int meshCount, trianglesAfterModifiers;
            public float metersPerUnit, sourceCameraClipStart;
            public float[] boundsMinBlender, boundsMaxBlender;
            public Surface[] materials;
            public Landmark[] landmarks;
        }

        [Serializable] public class LandmarkResult
        {
            public string name;
            public Vector3 blenderPosition, unityPosition;
        }

        [Serializable] public class Verification
        {
            public string unityVersion, sourceBlenderVersion, scene, checkedAtUtc;
            public bool passed, allMaterialsUseUrpLit, rootTransformIdentity;
            public bool paletteMatches, boundsMatch, landmarksMatch, triangleCountMatches;
            public int importedMeshCount, expectedMeshCount, ringCount, materialCount, triangles;
            public float cameraNearClip;
            public Vector3 boundsCenter, boundsSize;
            public LandmarkResult[] landmarks;
        }

        static Manifest ReadManifest() => JsonUtility.FromJson<Manifest>(
            File.ReadAllText("Assets/Art/scene-manifest.json"));

        static Color Hex(string value)
        {
            if (!ColorUtility.TryParseHtmlString("#" + value, out var color))
                throw new InvalidDataException("Invalid material color: " + value);
            return color;
        }

        static Material MaterialAsset(string name, Color color, float metal, float rough)
        {
            string path = "Assets/Art/Materials/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(material, path);
            }
            material.SetColor("_BaseColor", color);
            material.SetFloat("_Metallic", metal);
            material.SetFloat("_Smoothness", 1 - rough);
            EditorUtility.SetDirty(material);
            return material;
        }

        static void ConfigurePipeline()
        {
            const string rendererPath = "Assets/Settings/ChapterRenderer.asset";
            const string pipelinePath = "Assets/Settings/ChapterPipeline.asset";
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rendererPath);
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(renderer, rendererPath);
            }
            // Match the resources assigned by URP's Create Pipeline Asset menu.
            renderer.postProcessData = AssetDatabase.LoadAssetAtPath<PostProcessData>(
                "Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset");
            if (renderer.postProcessData == null)
                throw new InvalidDataException("URP post-processing resources are missing.");
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(pipelinePath);
            if (pipeline == null)
            {
                pipeline = UniversalRenderPipelineAsset.Create(renderer);
                AssetDatabase.CreateAsset(pipeline, pipelinePath);
            }
            pipeline.supportsHDR = true;
            pipeline.msaaSampleCount = 4;
            // URP enables main-light shadows by default; its public property
            // has an internal setter in Unity 6.3.
            pipeline.mainLightShadowmapResolution = 2048;
            pipeline.shadowDistance = 60;
            pipeline.shadowCascadeCount = 2;
            // These settings expose internal setters in URP 17.3. Use Unity's
            // serialized editor interface, as the pipeline Inspector does.
            var settings = new SerializedObject(pipeline);
            settings.FindProperty("m_MainLightShadowsSupported").boolValue = true;
            settings.FindProperty("m_SoftShadowsSupported").boolValue = true;
            settings.ApplyModifiedPropertiesWithoutUndo();
            GraphicsSettings.defaultRenderPipeline = pipeline;
            for (int i = 0; i < QualitySettings.names.Length; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = pipeline;
            }
            QualitySettings.SetQualityLevel(QualitySettings.names.Length - 1, true);
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.companyName = "synthesoul";
            PlayerSettings.productName = "First Ring - Chapter 01";
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 960;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            EditorSettings.serializationMode = SerializationMode.ForceText;
            EditorUtility.SetDirty(renderer);
            EditorUtility.SetDirty(pipeline);
        }

        [MenuItem("Book Projects/Chapter 01/Rebuild Unity Scene")]
        public static void Build()
        {
            foreach (string folder in new[] { "Assets/Art/Materials", "Assets/Settings", "Assets/Scenes" })
                Directory.CreateDirectory(folder);
            AssetDatabase.Refresh();
            ConfigurePipeline();
            Manifest manifest = ReadManifest();
            var palette = manifest.materials.ToDictionary(surface => surface.name,
                surface => MaterialAsset(surface.name, Hex(surface.hex), surface.metallic, surface.roughness));
            var importer = (ModelImporter)AssetImporter.GetAtPath(ModelPath);
            importer.globalScale = 1;
            importer.useFileScale = true;
            importer.bakeAxisConversion = true;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            importer.preserveHierarchy = true;
            importer.meshCompression = ModelImporterMeshCompression.Off;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            foreach (var pair in palette)
                importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), pair.Key), pair.Value);
            importer.SaveAndReimport();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var art = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath));
            art.name = "FirstRing";
            art.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            art.transform.localScale = Vector3.one;
            PrefabUtility.SaveAsPrefabAssetAndConnect(art, PrefabPath, InteractionMode.AutomatedAction);

            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Studio Floor (Unity)";
            floor.transform.position = new Vector3(0, -.39f, 0);
            floor.transform.localScale = Vector3.one * 20;
            Object.DestroyImmediate(floor.GetComponent<Collider>());
            floor.GetComponent<Renderer>().sharedMaterial = MaterialAsset("Backdrop", Hex("102D42"), 0, .9f);

            var camera = new GameObject("Main Camera (Unity)").AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.transform.position = new Vector3(12.5f, 12.8f, -18);
            camera.transform.LookAt(new Vector3(0, 2.5f, 0));
            camera.orthographic = true;
            camera.orthographicSize = 7.0125f;
            camera.nearClipPlane = .01f;
            camera.farClipPlane = 300;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Hex("102D42");
            camera.allowHDR = true;
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;

            var sun = Directional("Key Light", new Vector3(42, -32, 0), Hex("FFF1DB"), 2.2f);
            sun.shadows = LightShadows.Soft;
            sun.shadowBias = .03f;
            sun.shadowNormalBias = .15f;
            RenderSettings.sun = sun;
            Directional("Fill Light", new Vector3(38, 145, 0), Hex("BADFFF"), .7f);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = Hex("A1C9DD");
            RenderSettings.ambientEquatorColor = Hex("749596");
            RenderSettings.ambientGroundColor = Hex("424F52");
            RenderSettings.ambientIntensity = 1;
            RenderSettings.reflectionIntensity = .8f;

            const string volumePath = "Assets/Settings/ChapterVolume.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(volumePath);
            if (profile == null)
            {
                profile = ScriptableObject.CreateInstance<VolumeProfile>();
                AssetDatabase.CreateAsset(profile, volumePath);
            }
            if (!profile.TryGet<Tonemapping>(out var tone))
            {
                tone = profile.Add<Tonemapping>();
                AssetDatabase.AddObjectToAsset(tone, profile);
            }
            tone.mode.Override(TonemappingMode.ACES);
            EditorUtility.SetDirty(tone);
            EditorUtility.SetDirty(profile);
            var volume = new GameObject("Global Volume (Unity)").AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = profile;

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = art;
            if (SceneView.lastActiveSceneView != null) SceneView.lastActiveSceneView.FrameSelected();
            Verify();
        }

        static Light Directional(string name, Vector3 rotation, Color color, float intensity)
        {
            var light = new GameObject(name).AddComponent<Light>();
            light.type = LightType.Directional;
            light.transform.eulerAngles = rotation;
            light.color = color;
            light.intensity = intensity;
            return light;
        }

        [MenuItem("Book Projects/Chapter 01/Verify Saved Scene")]
        public static void Verify()
        {
            EditorSceneManager.OpenScene(ScenePath);
            var manifest = ReadManifest();
            var art = GameObject.Find("FirstRing");
            if (art == null) throw new InvalidDataException("FirstRing is missing from the scene.");
            var meshes = art.GetComponentsInChildren<MeshFilter>();
            var renderers = art.GetComponentsInChildren<MeshRenderer>();
            var materials = renderers.SelectMany(r => r.sharedMaterials).Distinct().ToArray();
            var bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            var transforms = art.GetComponentsInChildren<Transform>().ToDictionary(t => t.name);
            var landmarks = manifest.landmarks.Select(point => new LandmarkResult {
                name = point.name,
                blenderPosition = new Vector3(point.position[0], point.position[1], point.position[2]),
                unityPosition = transforms[point.name].position
            }).ToArray();
            bool rootIdentity = art.transform.position == Vector3.zero &&
                art.transform.rotation == Quaternion.identity && art.transform.localScale == Vector3.one;
            bool urp = materials.All(m => m != null && m.shader.name == "Universal Render Pipeline/Lit");
            int rings = transforms.Keys.Count(name => name.StartsWith("Ring_", StringComparison.Ordinal));
            bool paletteMatches = materials.Length == manifest.materials.Length &&
                manifest.materials.All(surface => materials.Any(material => material != null &&
                    material.name == surface.name &&
                    Vector4.Distance(material.GetColor("_BaseColor"), Hex(surface.hex)) < .0001f &&
                    Mathf.Abs(material.GetFloat("_Metallic") - surface.metallic) < .0001f &&
                    Mathf.Abs(material.GetFloat("_Smoothness") - (1 - surface.roughness)) < .0001f));
            var expectedMin = new Vector3(manifest.boundsMinBlender[0], manifest.boundsMinBlender[2], manifest.boundsMinBlender[1]);
            var expectedMax = new Vector3(manifest.boundsMaxBlender[0], manifest.boundsMaxBlender[2], manifest.boundsMaxBlender[1]);
            bool boundsMatch = Vector3.Distance(bounds.min, expectedMin) < .001f &&
                Vector3.Distance(bounds.max, expectedMax) < .001f;
            bool landmarksMatch = landmarks.All(point => Vector3.Distance(point.unityPosition,
                new Vector3(point.blenderPosition.x, point.blenderPosition.z, point.blenderPosition.y)) < .001f);
            int triangles = meshes.Sum(m => m.sharedMesh.triangles.Length / 3);
            bool triangleCountMatches = triangles == manifest.trianglesAfterModifiers;
            bool passed = meshes.Length == manifest.meshCount && rings == 5 && rootIdentity && urp &&
                paletteMatches && boundsMatch && landmarksMatch && triangleCountMatches &&
                Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).Length == 1 &&
                Mathf.Abs(Camera.main.nearClipPlane - .01f) < .00001f;
            var result = new Verification {
                unityVersion = Application.unityVersion,
                sourceBlenderVersion = manifest.blenderVersion,
                scene = ScenePath, checkedAtUtc = DateTime.UtcNow.ToString("O"), passed = passed,
                importedMeshCount = meshes.Length, expectedMeshCount = manifest.meshCount,
                ringCount = rings, materialCount = materials.Length,
                triangles = triangles, triangleCountMatches = triangleCountMatches,
                allMaterialsUseUrpLit = urp, rootTransformIdentity = rootIdentity,
                paletteMatches = paletteMatches, boundsMatch = boundsMatch, landmarksMatch = landmarksMatch,
                cameraNearClip = Camera.main.nearClipPlane,
                boundsCenter = bounds.center, boundsSize = bounds.size, landmarks = landmarks
            };
            Directory.CreateDirectory(Path.Combine(Chapter, "verification"));
            File.WriteAllText(Path.Combine(Chapter, "verification/unity-checks.json"), JsonUtility.ToJson(result, true) + "\n");
            Debug.Log("CHAPTER_VERIFICATION " + JsonUtility.ToJson(result));
            if (!passed) throw new InvalidDataException("Chapter verification failed; see verification/unity-checks.json.");
        }

        [MenuItem("Book Projects/Chapter 01/Capture Unity Preview")]
        public static void CapturePreview()
        {
            EditorSceneManager.OpenScene(ScenePath);
            // Opening a scene queues native renderer/light updates. The first
            // render request can also precede post-processing initialization;
            // render a warm-up frame, then capture on a later editor update.
            // Batch mode exits explicitly; do not pass -quit on the command line.
            bool previousAsyncCompilation = ShaderUtil.allowAsyncCompilation;
            ShaderUtil.allowAsyncCompilation = false;
            bool warmedUp = false;
            double readyAt = EditorApplication.timeSinceStartup + 3;
            EditorApplication.CallbackFunction capture = null;
            capture = () => {
                if (EditorApplication.isCompiling || EditorApplication.isUpdating ||
                    EditorApplication.timeSinceStartup < readyAt) return;
                try
                {
                    RenderPreview(warmedUp);
                    if (!warmedUp)
                    {
                        warmedUp = true;
                        readyAt = EditorApplication.timeSinceStartup + 1;
                        return;
                    }
                    EditorApplication.update -= capture;
                    ShaderUtil.allowAsyncCompilation = previousAsyncCompilation;
                    if (Application.isBatchMode) EditorApplication.Exit(0);
                }
                catch (Exception error)
                {
                    EditorApplication.update -= capture;
                    ShaderUtil.allowAsyncCompilation = previousAsyncCompilation;
                    Debug.LogException(error);
                    if (Application.isBatchMode) EditorApplication.Exit(1);
                }
            };
            EditorApplication.update += capture;
        }

        static void RenderPreview(bool saveImage)
        {
            var camera = Camera.main;
            var target = new RenderTexture(1600, 1200, 24, RenderTextureFormat.ARGB32);
            Texture2D texture = null;
            var previous = RenderTexture.active;
            try
            {
                target.antiAliasing = 4;
                target.Create();
                // StandardRequest runs the full pipeline, including lighting
                // globals and volumes. A single-camera request skips that setup.
                var request = new RenderPipeline.StandardRequest { destination = target };
                if (!RenderPipeline.SupportsRenderRequest(camera, request))
                    throw new InvalidOperationException("URP rendering is not available. Run with graphics enabled.");
                RenderPipeline.SubmitRenderRequest(camera, request);
                if (!saveImage)
                {
                    Debug.Log("CHAPTER_PREVIEW_WARMUP complete");
                    return;
                }
                RenderTexture.active = target;
                texture = new Texture2D(1600, 1200, TextureFormat.RGB24, false);
                texture.ReadPixels(new Rect(0, 0, 1600, 1200), 0, 0);
                texture.Apply();
                string path = Path.Combine(Chapter, "previews/unity-preview.png");
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(path, texture.EncodeToPNG());
                Debug.Log("CHAPTER_PREVIEW " + path);
            }
            finally
            {
                RenderTexture.active = previous;
                target.Release();
                if (texture != null) Object.DestroyImmediate(texture);
                Object.DestroyImmediate(target);
            }
        }
    }
}
