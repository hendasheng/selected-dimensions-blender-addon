import bpy
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh=bpy.data.meshes.new('TestMesh')
mesh.from_pydata([(x,y,z) for x in (-0.05,0.05) for y in (-0.1,0.1) for z in (-0.15,0.15)],[],[])
obj=bpy.data.objects.new('ScaledBox',mesh); bpy.context.scene.collection.objects.link(obj)
obj.scale=(2,3,4); obj.rotation_euler=(0.2,0.4,0.6)
coll=bpy.data.collections.new('Source'); child=bpy.data.objects.new('InstanceMesh',mesh); coll.objects.link(child)
inst=bpy.data.objects.new('CollectionInstance',None); inst.instance_type='COLLECTION'; inst.instance_collection=coll; inst.scale=(3,2,1); bpy.context.scene.collection.objects.link(inst)
bpy.context.view_layer.update()
import sys, importlib, tempfile, tomllib
root=Path(__file__).resolve().parents[1]
work=root.parent/'work'
work.mkdir(exist_ok=True)
repo_path=Path(tempfile.mkdtemp(prefix='extension_install_',dir=work))
repo=bpy.context.preferences.extensions.repos.new(name='Selected Dimensions Test',module='sd_extension_test',custom_directory=str(repo_path))
manifest=tomllib.loads((root/'selected_dimensions/blender_manifest.toml').read_text(encoding='utf-8'))
archive=root/'dist'/f"selected_dimensions-{manifest['version']}.zip"
result=bpy.ops.extensions.package_install_files(filepath=str(archive),repo=repo.module,enable_on_install=True)
assert result=={'FINISHED'},result
module='bl_ext.'+repo.module+'.selected_dimensions'
addon=importlib.import_module(module)
assert addon.__package__==module
assert not hasattr(addon,'bl_info')
installed=tomllib.loads((repo_path/'selected_dimensions/blender_manifest.toml').read_text(encoding='utf-8'))
assert installed['version']==manifest['version']
assert installed['maintainer']=='HenDaSheng'
assert installed['website']=='https://github.com/hendasheng/selected-dimensions-blender-addon'
assert not addon.state['enabled'] and addon.state['handle'] is None
assert bpy.context.window_manager.sd_axis_space=='WORLD'
bpy.context.window_manager.sd_axis_space='LOCAL'
bpy.ops.view3d.selected_dimensions_show(); bpy.ops.view3d.selected_dimensions_show()
ns={'collect_selected_bounds':addon.collect_selected_bounds}
def measure(selected,expected):
 for o in bpy.context.scene.objects: o.select_set(False)
 for o in selected: o.select_set(True)
 bounds=ns['collect_selected_bounds'](bpy.context)
 assert len(bounds)==len(expected),(len(bounds),len(expected))
 for b,e in zip(bounds,expected):
  delta=b['max']-b['min']; mat=b['object'].matrix_world.to_3x3()
  values=[(mat @ __import__('mathutils').Vector(tuple(delta[k] if k==axis else 0 for k in range(3)))).length*1000 for axis in range(3)]
  assert all(abs(a-c)<0.02 for a,c in zip(values,e)),(values,e)
measure([obj],[(200,600,1200)])
measure([inst],[(300,400,300)])
measure([],[])

bpy.context.window_manager.sd_axis_space='WORLD'
for ob in bpy.context.scene.objects: ob.select_set(False)
obj.select_set(True)
bounds=addon.collect_selected_bounds(bpy.context)
b=bounds[0]
actual=[v*1000 for v in b['max']-b['min']]
from mathutils import Vector
pts=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
expected=[(max(v[k] for v in pts)-min(v[k] for v in pts))*1000 for k in range(3)]
assert all(abs(a-e)<0.02 for a,e in zip(actual,expected)),(actual,expected)
assert b['matrix'].is_identity
bpy.context.window_manager.sd_axis_space='LOCAL'
measure([obj],[(200,600,1200)])


units=bpy.context.scene.unit_settings
for system,unit,scale,expected,label in [('METRIC','MILLIMETERS',1,1000,'mm'),('METRIC','CENTIMETERS',1,100,'cm'),('METRIC','METERS',0.001,0.001,'m'),('IMPERIAL','INCHES',1,39.37007874,'in'),('IMPERIAL','FEET',1,3.280839895,'ft'),('NONE','ADAPTIVE',1,1,'BU')]:
    units.system=system; units.length_unit=unit; units.scale_length=scale
    value,suffix=addon.scene_length(1,bpy.context.scene)
    assert abs(value-expected)<1e-5 and suffix==label,(value,suffix,expected,label)


prefs=bpy.context.preferences.view
prefs.use_translate_interface=True
prefs.language='en_US'
assert bpy.app.translations.pgettext_iface('Show Dimensions')=='Show Dimensions'
assert addon.SD_OT_show.bl_label=='Show Dimensions'
assert addon.SD_PT_panel.bl_category=='Dimensions'
prefs.language='zh_HANS'
translated=bpy.app.translations.pgettext_iface('Show Dimensions')
assert translated=='显示尺寸',repr(translated)
assert bpy.app.translations.pgettext_iface('Dimensions')!='Dimensions'
prefs.language='en_US'
assert bpy.app.translations.pgettext_iface('Show Dimensions')=='Show Dimensions'

bpy.ops.view3d.selected_dimensions_hide(); bpy.ops.view3d.selected_dimensions_hide()
bpy.ops.view3d.selected_dimensions_show()
addon.before_load(None)
assert not addon.state['enabled']
addon.unregister(); addon.register()
bpy.ops.preferences.addon_disable(module=module)
assert addon.state['handle'] is None
result=bpy.ops.extensions.package_uninstall(repo_directory=str(repo_path),pkg_id='selected_dimensions')
assert result=={'FINISHED'},result
assert not (repo_path/'selected_dimensions').exists()
bpy.context.preferences.extensions.repos.remove(repo)
print('ADDON_TEST_PASS',bpy.app.version_string,'EXTENSION ZIP install/enable/uninstall, manifest, English/Chinese, defaults, instances, units, lifecycle')
