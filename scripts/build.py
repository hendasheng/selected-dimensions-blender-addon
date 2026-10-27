"""Build a Blender Extension ZIP from its manifest (Python 3.11+)."""
import argparse
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(tag=None):
    package = ROOT / "selected_dimensions"
    manifest_path = package / "blender_manifest.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest["version"]
    if tag and tag != f"v{version}":
        raise SystemExit(f"Tag {tag!r} does not match extension version v{version}")
    source = package / "__init__.py"
    compile(source.read_text(encoding="utf-8"), str(source), "exec")
    out = ROOT / "dist" / f"{manifest['id']}-{version}.zip"
    out.parent.mkdir(exist_ok=True)
    # Extension metadata and entry point belong at the archive root.
    files = [(manifest_path, "blender_manifest.toml"),
             (source, "__init__.py"), (ROOT / "LICENSE", "LICENSE")]
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in files:
            item = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o644 << 16
            archive.writestr(item, path.read_bytes())
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == [name for _, name in files]
    print(out)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Require the release tag to match the manifest version")
    build(parser.parse_args().tag)
