"""Build an installable ZIP using the version in bl_info (standard library only)."""
import argparse
import ast
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(tag=None):
    source = ROOT / "selected_dimensions" / "__init__.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    info = next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "bl_info" for t in node.targets))
    version = ".".join(map(str, info["version"]))
    if tag and tag != f"v{version}":
        raise SystemExit(f"Tag {tag!r} does not match add-on version v{version}")
    compile(source.read_text(encoding="utf-8-sig"), str(source), "exec")
    out = ROOT / "dist" / f"selected_dimensions-{version}.zip"
    out.parent.mkdir(exist_ok=True)
    files = [(source, "selected_dimensions/__init__.py"),
             (ROOT / "LICENSE", "selected_dimensions/LICENSE")]
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
    parser.add_argument("--tag", help="Require a matching release tag, e.g. v0.1.0")
    build(parser.parse_args().tag)
