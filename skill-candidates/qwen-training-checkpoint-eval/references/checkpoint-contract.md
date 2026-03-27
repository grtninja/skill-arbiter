# Checkpoint Contract

Each continuation batch should leave behind:

- `batch_sources.json`
- `batch_sources.txt`
- `trainer.report.json`
- `checkpoint.eval.json`
- `adapter/`

## `checkpoint.eval.json`

Expected fields:

- `sample_count`
- `json_parse_success_count`
- `adult_context_match_count`
- `penny_affinity_match_count`
- `descriptor_overlap_mean`
- `samples[]`

Each sample should preserve:

- batch record id
- exact media paths
- expected teacher text
- generated checkpoint text
- parsed expected payload
- parsed generated payload

## Eval Lane Contract

When mounting a saved adapter on the Radeon eval lane:

1. `/health` must return `ok=true`
2. `/health.runtime.adapter_loaded` must be `true`
3. `/v1/models` must expose the private local alias for the trained lane

If these fail, do not promote the checkpoint.
