# Troubleshooting

## AssetBundle Load Failure

Symptom:

- Unity reports `can't be loaded because it was not built with the right version or build target`.

Action:

- Do not use direct `AssetBundle.LoadFromFile` for extraction.
- Export the bundle through AssetRipper first, then operate on exported `.anim` assets.

## Dummy Script Stubs in AssetRipper Export

Symptom:

- Classes like `VrmAnimationExporter` exist as dummy placeholders and exporter methods are missing.

Action:

1. Disable the exported `Assets/Scripts` tree.
2. Patch `Packages/manifest.json` to use local UniVRM packages:
   - `com.vrmc.gltf` -> `file:<univrm>/Assets/UniGLTF`
   - `com.vrmc.vrm` -> `file:<univrm>/Assets/VRM10`

## UniGLTF TestRunner Compile Errors

Symptom:

- Missing `UnityEditor.TestTools` or `NUnit` types from `UniGLTF/Editor/TestRunner`.

Action:

- Move `UniGLTF/Editor/TestRunner` outside the package root.

## Missing Hips Bone During Export

Symptom:

- Summary row error: `Humanoid mapping is missing Hips bone.`

Action:

- Use the provided `assets/VroidVrmaBatch.cs` which contains hips-name fallback resolution.
