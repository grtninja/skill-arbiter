#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UniGLTF;
using UniHumanoid;
using UniVRM10;
using UnityEditor;
using UnityEngine;

public static class VroidVrmaBatch
{
    private const string ArgOutDir = "--out-dir=";
    private const string ArgPrefab = "--prefab=";
    private const string ArgClipRoots = "--clip-roots=";
    private const string ArgLimit = "--limit=";
    private const string ArgNameFilter = "--name-filter=";

    public static void Run()
    {
        var args = Environment.GetCommandLineArgs();
        var outDir = GetArg(args, ArgOutDir, string.Empty);
        var prefabPath = GetArg(args, ArgPrefab, "Assets/Resources/animations/female/unitychan_WAIT00.prefab");
        var clipRootsRaw = GetArg(args, ArgClipRoots,
            "Assets/Resources/animations/female;Assets/Resources/animations/male;Assets/Resources/animations/pv/female;Assets/Resources/animations/pv/male");
        var nameFilter = GetArg(args, ArgNameFilter, string.Empty);
        var limitRaw = GetArg(args, ArgLimit, "0");

        if (string.IsNullOrWhiteSpace(outDir))
        {
            throw new InvalidOperationException("Missing --out-dir=<absolute path>");
        }

        if (!int.TryParse(limitRaw, out var limit) || limit < 0)
        {
            limit = 0;
        }

        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        if (prefab == null)
        {
            throw new InvalidOperationException($"Avatar prefab not found: {prefabPath}");
        }

        var clipRoots = clipRootsRaw
            .Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries)
            .Select(root => root.Trim())
            .Where(root => !string.IsNullOrWhiteSpace(root))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        if (clipRoots.Length == 0)
        {
            throw new InvalidOperationException("No clip roots resolved. Pass --clip-roots=Assets/...;Assets/...");
        }

        var clipPaths = AssetDatabase.FindAssets("t:AnimationClip", clipRoots)
            .Select(AssetDatabase.GUIDToAssetPath)
            .Where(path => path.EndsWith(".anim", StringComparison.OrdinalIgnoreCase))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        Directory.CreateDirectory(outDir);

        var summary = new List<string>
        {
            "index\tassetPath\toutputPath\tclipName\tstatus\tmessage"
        };

        var success = 0;
        var failed = 0;
        var seen = 0;

        for (var i = 0; i < clipPaths.Length; i++)
        {
            var clipPath = clipPaths[i];
            if (!string.IsNullOrWhiteSpace(nameFilter) &&
                clipPath.IndexOf(nameFilter, StringComparison.OrdinalIgnoreCase) < 0)
            {
                continue;
            }

            if (limit > 0 && seen >= limit)
            {
                break;
            }
            seen += 1;

            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
            if (clip == null)
            {
                failed += 1;
                summary.Add($"{seen}\t{clipPath}\t\t\tfailed\tunable to load AnimationClip");
                continue;
            }

            var outputName = BuildOutputName(clipPath, clip.name);
            var outputPath = Path.Combine(outDir, outputName + ".vrma");

            try
            {
                var bytes = ExportClipToVrma(prefab, clip);
                File.WriteAllBytes(outputPath, bytes);
                success += 1;
                summary.Add($"{seen}\t{clipPath}\t{outputPath}\t{clip.name}\tok\t{bytes.Length.ToString(CultureInfo.InvariantCulture)} bytes");
            }
            catch (Exception ex)
            {
                failed += 1;
                summary.Add($"{seen}\t{clipPath}\t{outputPath}\t{clip.name}\tfailed\t{SanitizeMessage(ex.Message)}");
            }
        }

        var summaryPath = Path.Combine(outDir, "vrma_export_summary.tsv");
        File.WriteAllLines(summaryPath, summary, Encoding.UTF8);

        Debug.Log($"VroidVrmaBatch complete. success={success}, failed={failed}, scanned={clipPaths.Length}, processed={seen}, outDir={outDir}");
    }

    private static string BuildOutputName(string clipPath, string clipName)
    {
        var normalized = clipPath.Replace('\\', '/');
        var marker = "Assets/Resources/animations/";
        var prefix = "misc";
        var idx = normalized.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
        if (idx >= 0)
        {
            var relative = normalized.Substring(idx + marker.Length);
            var slash = relative.LastIndexOf('/');
            if (slash > 0)
            {
                var folder = relative.Substring(0, slash).Replace('/', '_');
                if (!string.IsNullOrWhiteSpace(folder))
                {
                    prefix = folder;
                }
            }
        }

        var safeClip = SanitizeFileName(clipName);
        if (string.IsNullOrWhiteSpace(safeClip))
        {
            safeClip = "clip";
        }
        return prefix + "__" + safeClip;
    }

    private static byte[] ExportClipToVrma(GameObject avatarPrefab, AnimationClip clip)
    {
        var instance = PrefabUtility.InstantiatePrefab(avatarPrefab) as GameObject;
        if (instance == null)
        {
            throw new InvalidOperationException("Failed to instantiate avatar prefab.");
        }

        try
        {
            var animator = instance.GetComponentInChildren<Animator>(true);
            if (animator == null)
            {
                throw new InvalidOperationException("Animator was not found on prefab instance.");
            }
            if (animator.avatar == null || !animator.avatar.isHuman)
            {
                throw new InvalidOperationException("Animator avatar is missing or non-humanoid.");
            }

            animator.Rebind();

            var boneMap = new Dictionary<HumanBodyBones, Transform>();
            foreach (HumanBodyBones bone in Enum.GetValues(typeof(HumanBodyBones)))
            {
                if (bone == HumanBodyBones.LastBone)
                {
                    continue;
                }

                var t = animator.GetBoneTransform(bone);
                if (t != null)
                {
                    boneMap[bone] = t;
                }
            }

            if (!boneMap.TryGetValue(HumanBodyBones.Hips, out var hips))
            {
                hips = FindLikelyHips(instance.transform);
                if (hips == null)
                {
                    throw new InvalidOperationException("Humanoid mapping is missing Hips bone.");
                }
                boneMap[HumanBodyBones.Hips] = hips;
            }

            var data = new ExportingGltfData();
            using var exporter = new VrmAnimationExporter(data, new GltfExportSettings());
            exporter.Prepare(instance);

            exporter.Export(vrma =>
            {
                vrma.SetPositionBoneAndParent(hips, instance.transform);

                foreach (var kv in boneMap)
                {
                    var parent = ResolveParentForBone(boneMap, kv.Key) ?? instance.transform;
                    vrma.AddRotationBoneAndParent(kv.Key, kv.Value, parent);
                }

                var frameRate = clip.frameRate > 0f ? clip.frameRate : 30f;
                var duration = Mathf.Max(clip.length, 1f / frameRate);
                var frameCount = Mathf.Max(2, Mathf.CeilToInt(duration * frameRate) + 1);

                AnimationMode.StartAnimationMode();
                try
                {
                    for (var i = 0; i < frameCount; i++)
                    {
                        var t = Mathf.Min(duration, i / frameRate);
                        AnimationMode.SampleAnimationClip(instance, clip, t);
                        vrma.AddFrame(TimeSpan.FromSeconds(t));
                    }
                }
                finally
                {
                    AnimationMode.StopAnimationMode();
                }
            });

            return data.ToGlbBytes();
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static Transform ResolveParentForBone(Dictionary<HumanBodyBones, Transform> map, HumanBodyBones bone)
    {
        Vrm10HumanoidBones current;
        try
        {
            current = Vrm10HumanoidBoneSpecification.ConvertFromUnityBone(bone);
        }
        catch
        {
            return null;
        }

        while (true)
        {
            if (current == Vrm10HumanoidBones.Hips)
            {
                return null;
            }

            var spec = Vrm10HumanoidBoneSpecification.GetDefine(current);
            if (!spec.ParentBone.HasValue)
            {
                return null;
            }

            current = spec.ParentBone.Value;
            var unityParent = Vrm10HumanoidBoneSpecification.ConvertToUnityBone(current);
            if (map.TryGetValue(unityParent, out var found))
            {
                return found;
            }
        }
    }

    private static Transform FindLikelyHips(Transform root)
    {
        if (root == null)
        {
            return null;
        }

        var all = root.GetComponentsInChildren<Transform>(true);
        var exact = all.FirstOrDefault(t => string.Equals(t.name, "Hips", StringComparison.OrdinalIgnoreCase));
        if (exact != null)
        {
            return exact;
        }

        var contains = all
            .Where(t => t.name.IndexOf("hip", StringComparison.OrdinalIgnoreCase) >= 0)
            .OrderBy(t => t.name.Length)
            .FirstOrDefault();
        return contains;
    }

    private static string GetArg(string[] args, string prefix, string fallback)
    {
        var value = args.FirstOrDefault(a => a.StartsWith(prefix, StringComparison.OrdinalIgnoreCase));
        return value != null ? value.Substring(prefix.Length) : fallback;
    }

    private static string SanitizeFileName(string value)
    {
        var invalid = Path.GetInvalidFileNameChars();
        var sb = new StringBuilder(value.Length);
        foreach (var ch in value)
        {
            if (invalid.Contains(ch) || char.IsControl(ch))
            {
                sb.Append('_');
            }
            else
            {
                sb.Append(ch);
            }
        }
        return sb.ToString().Trim('_', ' ');
    }

    private static string SanitizeMessage(string message)
    {
        if (string.IsNullOrWhiteSpace(message))
        {
            return "unknown error";
        }
        return message.Replace('\r', ' ').Replace('\n', ' ').Replace('\t', ' ').Trim();
    }
}
#endif
