# AGENTS.md

README_CN.md is the source of truth for user-facing documentation. Update README.md in the same change, keeping both documents aligned in structure and meaning.

Direct users to GitHub Releases and the installable add-on ZIP, not the automatically generated source code ZIP.

The add-on version in selected_dimensions/__init__.py is the single source of truth. Release tags must match vMAJOR.MINOR.PATCH. Run scripts/build.py before releasing, and test Blender lifecycle and dimensions with scripts/test_blender.py in Blender 5.0 and 5.2.

Keep dimensions disabled by default and use world coordinates by default. Preserve selection-only measurement, collection-instance support, scene units and Chinese/English translations.
