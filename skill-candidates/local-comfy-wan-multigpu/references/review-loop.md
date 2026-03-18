# Review Loop

Every render should end with an actual visual review pass.

## Minimum Review Artifacts

- output clip
- saved prompt JSON
- saved result JSON
- extracted review frames
- one review sheet image

## Review Steps

1. Open the export folder in Explorer.
2. Build a review sheet from the output clip.
3. Load the review sheet into an image viewer or the local image-view tool and inspect it directly.
4. If a local screenshot capability is available, capture the visible result viewer state for operator evidence.
5. Judge the render on:
   - composition preserved
   - identity preserved
   - face coherence
   - hands or body integrity if visible
   - temporal consistency across extracted frames
   - motion speed feels intentional rather than slow, floaty, or under-cranked
   - whether the clip is long enough to be meaningful
6. If the shot is intended to loop, judge the forward clip first.
7. Only build the reverse leg after the forward clip is approved.
8. Prefer assembling forward + reverse in CapCut or another editor unless a local loop-aware model path is being tested on purpose.

## Failure Classification

- `source_choice`: bad input still
- `staging_choice`: bad pad/fit/crop decision
- `prompt_choice`: weak or conflicting prompt
- `workflow_choice`: wrong template or node graph
- `runtime_limit`: VRAM or model limit
- `quality_gate`: render completed but is not good enough
