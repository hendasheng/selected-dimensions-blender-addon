# AGENTS.md

Read docs/AGENT_HANDOFF.md before changing this repository. Keep it current when implementation, packaging, verification or release status changes.

## User documentation

- README_CN.md is the source of truth; update README.md in the same change with matching structure and meaning.
- READMEs are for end users. Put implementation details, build commands, release procedures, verification records and agent context in docs/AGENT_HANDOFF.md.
- Do not hard-code release versions, versioned ZIP filenames, tags or local machine paths in user documentation. Direct users to the latest GitHub Release and describe the package filename pattern.
- State compatibility as Blender 5+. Keep exact tested versions in the handoff document, distinguishing tested coverage from the compatibility target.
- Check both READMEs for stale version numbers, asymmetric changes, broken image links and duplicated maintenance details before committing.
- Chinese and English READMEs have separate cover images under docs/images/.

## Product and releases

- Default dimensions off; default world coordinates.
- Preserve selection-only measurements, collection-instance support, scene units, Chinese/English UI and caching.
- selected_dimensions/blender_manifest.toml is the single version source. Tags must match vMAJOR.MINOR.PATCH. Do not restore legacy bl_info metadata. Extension archives must have blender_manifest.toml and __init__.py at their root.
- Do not move published tags or claim GitHub Actions / Releases succeeded without observing the result.
