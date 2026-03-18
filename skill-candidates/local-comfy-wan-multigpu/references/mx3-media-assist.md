# MX3 Media Assist

Use MX3 as a sidecar for source scoring, QC, masks, and mouth-region analysis.

Do not treat MX3 as the primary generator.

Preferred roles:

- `face-yunet`, `face-landmarks`, `face-headpose`, `face-eye-state`
  - source preflight
  - face-box quality
  - mouth ROI extraction
  - blink / frozen-eye checks
- `pose-simcc`, `pose-3d-omz`
  - body-rigidity checks
  - shoulder / torso motion scoring
- `emotion-ferplus`, `face-expression-mobilefacenety`
  - expression drift checks between variants
- `segmentation-bisenet`, `depth-hr`
  - repair masks
  - depth-aware planning
- `DaSiamRPN` tracker pair
  - stable face/mouth ROI tracking across frames
- `audio-speech-enhancement`
  - recorded/noisy voice cleanup only

If the MX3 runtime is down, record that explicitly and continue with the normal Comfy / MuseTalk / CapCut loop instead of pretending the assist plane is active.
