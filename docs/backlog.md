# Pipeline Tools Backlog

## Templates
- VFX episodic template (plates, matchmove, layout, FX, lighting, comp, delivery; add `vfx_episodic` key and `VF` prefix).
- Marketing/campaign template (briefs, creative, production files, exports/deliverables; define key/prefix).

## CLI / UX
- Allow configuring custom template roots via config/env without code changes.
- Improve status/phase flexibility (e.g., configurable asset/shot status sets).
- Add richer search/filter (by tags/status/kind) across assets/shots/versions.

## Ops
- Optional preflight that validates creative root permissions before scaffolding.
- CLI flag to show current show and DB path quickly (shortcut to `shows info` + `doctor` basics).

## Integration ideas
- Optional DCC hooks (file naming helpers, publish stubs) while keeping CLI thin.
- Export summaries in JSON/CSV for downstream tools.
