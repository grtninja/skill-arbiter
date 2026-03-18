# Source Selection Rules

## Reject These Inputs

- mouth-only crops
- chin-only crops
- heavily center-cropped posters reused from another workflow
- references that cut off the eyes or forehead unless that crop is intentional
- blurry or compressed exports when a cleaner original exists

## Prefer These Inputs

- full face with hairline and chin visible
- face plus shoulders
- torso or full-character references with clean subject separation
- neutral or lightly expressive poses for first-pass animation tests
- images with enough breathing room to survive square or video framing

## Staging Rule

Default to `fit` or `pad` transforms before any crop. Only crop when the user has seen the staged frame or explicitly asked for that framing.
