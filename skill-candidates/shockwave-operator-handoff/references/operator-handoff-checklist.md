# Shockwave Operator Handoff Checklist

Use this reference when Project Shockwave changes affect what the operator sees or relies on during startup and live use.

## Required Handoff Surfaces

1. startup wrapper and visible dashboard launcher
2. control rail contract block
3. chat/status strip
4. active-service and phase labels
5. voice-path and playback recovery behavior

## Failure Patterns

- startup proof passes but the dashboard no longer reflects the same authority model
- control-plane or display-host labels drift from runtime truth
- degraded or offline services appear healthy in the UI
- transcript or tool-trace continuity breaks across mode switches
- voice or playback recovery regresses after interrupted speech cues
