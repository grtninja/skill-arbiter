# Risk Heuristics

## Signal Families

- destructive command patterns
- unsafe shell invocation (`shell=True`, `os.system`)
- network activity indicators (`curl`, `wget`, `http://`, `https://`)
- absolute path indicators
- repository scan command indicators (`rg`)
- bounded scan hints (`safe-mass-index-core`, budget flags)
- file mutation indicators in scripts

## Scoring Intent

Higher scores indicate larger probable impact and stricter rollout controls.

## Risk Levels

- `low`: informational only
- `medium`: guardrails recommended
- `high`: explicit acknowledgement required
- `critical`: block by default until remediation

## Output Contract Highlights

Per skill:

- `risk_score`
- `risk_level`
- `signals`
- `predicted_impact`
- `reason_codes`
- `baseline_score`
- `risk_delta`
- `ack_required`
