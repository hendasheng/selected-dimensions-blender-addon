"""Check the distribution archive without importing Blender."""
from pathlib import Path
import ast
import tomllib
import zipfile
from build import build

root=Path(__file__).resolve().parents[1]
manifest=tomllib.loads((root/'selected_dimensions/blender_manifest.toml').read_text(encoding='utf-8'))
archive=build(tag='v'+manifest['version'])
with zipfile.ZipFile(archive) as package:
    assert set(package.namelist())=={'blender_manifest.toml','__init__.py','LICENSE'}
    parsed=tomllib.loads(package.read('blender_manifest.toml').decode('utf-8'))
    assert parsed==manifest
    assert parsed['id']=='selected_dimensions'
    assert parsed['maintainer']=='HenDaSheng'
    assert parsed['blender_version_min']=='5.0.0'
    assert parsed['website']=='https://github.com/hendasheng/selected-dimensions-blender-addon'
    assert parsed['type']=='add-on'
    tree=ast.parse(package.read('__init__.py').decode('utf-8'))
    assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bl_info' for t in n.targets) for n in tree.body)
try:
    build(tag='v0.0.0-invalid')
except SystemExit:
    pass
else:
    raise AssertionError('Mismatched tag was accepted')
print('EXTENSION_PACKAGE_TEST_PASS',manifest['version'])
