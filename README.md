# Selected Dimensions

![Selected Dimensions](docs/images/selected-dimensions-blender-addon-en.png)

Blender add-on that displays the length, width and height of selected objects and collection instances in the 3D View.

[中文文档](README_CN.md)

## Features

- Measures selected objects only; multiple selections are measured separately.
- Supports collection instances, measuring each selected instance as a whole.
- Switches between local and world coordinates.
- Follows scene units and unit scale, supporting metric and imperial units.
- Chinese / English interface follows Blender language settings.
- Adjustable font size, decimal places and update interval, with cached measurements to reduce repeated work.
- Dimensions are off by default; world coordinates are the default.

## Installation

1. Go to [Releases](https://github.com/hendasheng/selected-dimensions-blender-addon/releases).
2. Download the `selected_dimensions-0.1.0.zip` add-on package.
3. In Blender, open Edit > Preferences > Add-ons > Install from Disk.
4. Select the add-on ZIP and enable Selected Dimensions.

Download the add-on package, not GitHub's automatically generated Source code ZIP.

## Panel Location

3D View > press N to open the Sidebar > Dimensions (translated when using a Chinese interface).

## Usage

1. Select one or more objects or collection instances in Object Mode.
2. Click Show Dimensions.
3. Choose Local or World coordinates and adjust the font size, decimal places and update interval as needed.
4. Click Hide Dimensions to remove annotations; deselecting also hides the corresponding annotations.

## Notes

- Compatible with Blender 5.0 and 5.2.
- X, Y and Z represent length, width and height in the chosen coordinate system; they are not sorted by magnitude.
- World mode measures a world-axis-aligned bounding box; Local mode measures along the object's own axes, including scale.
- Annotations are viewport overlays. They do not appear in renders or add text or lines to the model.
- Opening another file turns off annotations. Click Show Dimensions again when needed.
- Initial measurements or geometry changes in complex instances may take longer; increase the update interval if needed.

## Packaging and Releases

Build locally (Python 3.10+, no third-party dependencies):

```sh
python scripts/build.py
```

The package is written to `dist/selected_dimensions-0.1.0.zip`. The version is read automatically from the add-on's `bl_info`.

Pushing a tag such as `v0.1.0` makes GitHub Actions validate the tag against the add-on version, build the package and upload it to a GitHub Release.
You can also run Package and Release manually in Actions to download a build artifact.

For future releases, update the version in `selected_dimensions/__init__.py`, commit it and push the matching tag.

## Repository Structure

- `selected_dimensions/__init__.py`: Add-on source.
- `scripts/build.py`: Version validation and package builder.
- `scripts/test_blender.py`: Functional checks for Blender background mode.
- `.github/workflows/release.yml`: Automated packaging and release workflow.
- `README_CN.md` / `README.md`: Chinese and English documentation.
- `LICENSE`: MIT license.
