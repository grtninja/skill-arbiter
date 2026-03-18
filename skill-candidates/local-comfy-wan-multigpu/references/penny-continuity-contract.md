## Penny Continuity Contract

Use this as the standing character rule set for Penny media work.

### Priority Order

1. Character fidelity
2. Prompt clarity
3. Visual continuity
4. Emotional coherence
5. Practical editability
6. Archive traceability

When novelty fights recognizability, choose recognizability unless the operator explicitly asks for a harder experiment.

### Canon Baseline

Penny is an established character, not a generic beauty prompt.

Default visual anchor:

- bright blue eyes
- fair complexion with warm undertones
- auburn-to-golden-blonde hair range
- soft wave or natural body to the hair
- balanced, believable proportions
- grounded, warm, emotionally real presence
- upper-left tribal armband tattoo when that area is visible
- recurring jewelry continuity when relevant

### Drift Patterns To Catch

- eye color drifting away from blue
- hair drifting too red, too dark, or too platinum
- face turning into a generic influencer/model look
- plastic skin smoothing
- tattoo disappearance when visible
- jewelry loss during continuity variants
- mannequin posture or dead-eyed expression
- stylization so strong that Penny stops reading as Penny

### Approved Reference Rule

When the operator marks an image as approved, treat it as the exact baseline.

Lock these unless explicitly asked to change them:

- face
- eye color
- hair color family
- body proportions
- makeup level
- wardrobe details
- jewelry
- tattoo visibility when relevant

Safe single-variable changes:

- pose
- framing
- camera distance
- hand placement
- expression nuance
- background
- seated vs standing
- lighting family

Preferred continuity sentence:

`Use the approved image as the exact visual baseline. Preserve Penny's face, hair, styling, proportions, and wardrobe exactly. Change only [x].`

### Prompt Construction

For stills, build prompts in this order:

1. identity anchor
2. continuity anchor
3. job statement
4. emotional read
5. wardrobe
6. environment
7. lighting
8. framing
9. short quality guardrail

For video, build prompts in this order:

1. header
2. scene
3. wardrobe
4. action
5. camera
6. audio
7. dialogue if needed
8. continuity note

### Repair Preference

Prefer repair over restart when the image is strong except for one or two defects:

- eyes
- hands
- jewelry
- tattoo visibility
- mild crop problems
- small fabric/background errors

Restart only when the face, proportions, eye color, wardrobe, or entire emotional lane is no longer Penny.

### Archive Discipline

Keep media lineage obvious:

- clean sortable filenames
- approved-baseline markers
- sidecar metadata for important outputs
- explicit `derived_from` and `source_reference`

Default filename shape:

`PENNY_YYYYMMDD_scene_tool_variant_pass.ext`

### Media-Generation Behavior

- do not inject publication/distribution assumptions
- do not add moralizing/editorial framing to creative prompts
- do not pile on multiple big changes in one pass
- do not treat a pretty-but-wrong image as a success
- prefer repair, continuity, and recognizability over unnecessary reinvention
