bl_info = {
    "name": "Selected Dimensions",
    "author": "HenDaSheng",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "3D View > Sidebar > Dimensions",
    "description": "Measure selected objects and instances in local or world space using scene units",
    "category": "3D View",
}
import bpy, gpu, blf, time
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

_ZH_TRANSLATIONS={('*', 'Show Dimensions'): '显示尺寸', ('Operator', 'Show Dimensions'): '显示尺寸', ('*', 'Hide Dimensions'): '关闭尺寸', ('Operator', 'Hide Dimensions'): '关闭尺寸', ('*', 'Measure selected objects; measure each collection instance as a whole'): '仅标注选中物体，集合实例按整体测量', ('Operator', 'Measure selected objects; measure each collection instance as a whole'): '仅标注选中物体，集合实例按整体测量', ('*', 'Dimensions'): '尺寸', ('Operator', 'Dimensions'): '尺寸', ('*', 'Coordinate Space'): '坐标系', ('Operator', 'Coordinate Space'): '坐标系', ('*', 'Local'): '物体坐标', ('Operator', 'Local'): '物体坐标', ('*', 'World'): '世界坐标', ('Operator', 'World'): '世界坐标', ('*', 'Measure along the object local X, Y and Z axes'): '沿物体自身的 X、Y、Z 轴测量', ('Operator', 'Measure along the object local X, Y and Z axes'): '沿物体自身的 X、Y、Z 轴测量', ('*', 'Measure the bounding box along the world X, Y and Z axes'): '沿世界 X、Y、Z 轴测量包围盒', ('Operator', 'Measure the bounding box along the world X, Y and Z axes'): '沿世界 X、Y、Z 轴测量包围盒', ('*', 'X Length · Y Width · Z Height'): 'X 长 · Y 宽 · Z 高', ('Operator', 'X Length · Y Width · Z Height'): 'X 长 · Y 宽 · Z 高', ('*', 'Units: Follow Scene Settings'): '单位：跟随场景设置', ('Operator', 'Units: Follow Scene Settings'): '单位：跟随场景设置', ('*', 'Selection only; collection instances supported'): '仅显示选中物体；支持集合实例', ('Operator', 'Selection only; collection instances supported'): '仅显示选中物体；支持集合实例', ('*', 'Font Size'): '字号', ('Operator', 'Font Size'): '字号', ('*', 'Decimal Places'): '小数位', ('Operator', 'Decimal Places'): '小数位', ('*', 'Update Interval (s)'): '重算间隔（秒）', ('Operator', 'Update Interval (s)'): '重算间隔（秒）', ('*', 'Recalculate only when geometry changes; increase for complex scenes'): '仅模型发生变化时重算；复杂场景可增大此值', ('Operator', 'Recalculate only when geometry changes; increase for complex scenes'): '仅模型发生变化时重算；复杂场景可增大此值', ('*', 'Measured along world axes'): '沿世界坐标轴测量', ('Operator', 'Measured along world axes'): '沿世界坐标轴测量', ('*', 'Measured along local axes'): '沿物体自身坐标轴测量', ('Operator', 'Measured along local axes'): '沿物体自身坐标轴测量', ('*', 'Select an object to measure'): '请选择需要测量的物体', ('Operator', 'Select an object to measure'): '请选择需要测量的物体', ('*', 'Annotation error; hide and show dimensions to retry'): '标注遇到错误，请关闭后重试', ('Operator', 'Annotation error; hide and show dimensions to retry'): '标注遇到错误，请关闭后重试', ('*', 'Measure selected objects and instances in local or world space using scene units'): '显示选中模型与实例尺寸，支持物体/世界坐标和场景单位', ('Operator', 'Measure selected objects and instances in local or world space using scene units'): '显示选中模型与实例尺寸，支持物体/世界坐标和场景单位'}
TRANSLATIONS={'zh_HANS':_ZH_TRANSLATIONS,'zh_CN':_ZH_TRANSLATIONS}

state={'enabled':False,'handle':None,'error':None,'measurements':[], 'dirty':True,'cache':[], 'signature':None,'last_update':0.0}

def redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type=='VIEW_3D': area.tag_redraw()

def dimensions_changed(scene, depsgraph):
    state['dirty']=True

def stop():
    state['enabled']=False
    handle=state.get('handle')
    if handle is not None:
        try: bpy.types.SpaceView3D.draw_handler_remove(handle,'WINDOW')
        except (ValueError,ReferenceError): pass
    state.update(handle=None,cache=[],signature=None,measurements=[])
    if dimensions_changed in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(dimensions_changed)
    redraw()

@persistent
def before_load(dummy):
    stop()

def start():
    stop()
    # Stop earlier standalone scripts without changing any scene objects.
    for key in ('codex_selected_dimensions_v2','codex_dimension_overlay_v1'):
        old=bpy.app.driver_namespace.get(key)
        if type(old) is dict:
            old['enabled']=False
            handle=old.get('handle')
            if handle is not None:
                try: bpy.types.SpaceView3D.draw_handler_remove(handle,'WINDOW')
                except (ValueError,ReferenceError): pass
            old['handle']=None
            callback=old.get('update_handler')
            if callback in bpy.app.handlers.depsgraph_update_post:
                bpy.app.handlers.depsgraph_update_post.remove(callback)
    state.update(enabled=True,dirty=True,last_update=0.0,error=None)
    state['handle']=bpy.types.SpaceView3D.draw_handler_add(draw_selected_dimensions,(),'WINDOW','POST_PIXEL')
    if dimensions_changed not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(dimensions_changed)
    redraw()

def collect_selected_bounds(ctx):
    selected = [o for o in ctx.selected_objects if o.visible_get(view_layer=ctx.view_layer)]
    if not selected:
        return []
    world = ctx.window_manager.sd_axis_space == 'WORLD'
    targets = {o.as_pointer(): {'object':o,'inverse':Matrix.Identity(4) if world else o.matrix_world.inverted_safe(),'matrix':Matrix.Identity(4) if world else o.matrix_world.copy(),'min':None,'max':None} for o in selected}
    dg = ctx.evaluated_depsgraph_get()
    for item in dg.object_instances:
        if not item.show_self:
            continue
        obj = item.object
        if obj.type not in {'MESH','CURVE','SURFACE','FONT','META'}:
            continue
        if item.is_instance:
            parent = item.parent
            target = targets.get(parent.original.as_pointer()) if parent else None
        else:
            target = targets.get(obj.original.as_pointer())
        if target is None:
            continue
        transform = target['inverse'] @ item.matrix_world
        # Fast bounds for a mesh measured on its own axes.
        if not item.is_instance:
            corners=tuple(tuple(p) for p in obj.bound_box)
            if all(p==(-1.0,-1.0,-1.0) for p in corners):
                continue
            points=np.array(corners,dtype=np.float64)
        elif obj.type=='MESH' and obj.data and len(obj.data.vertices):
            coords=np.empty(len(obj.data.vertices)*3,dtype=np.float32)
            obj.data.vertices.foreach_get('co',coords)
            points=coords.reshape((-1,3))
        else:
            corners=tuple(tuple(p) for p in obj.bound_box)
            if all(p==(-1.0,-1.0,-1.0) for p in corners):
                continue
            points=np.array(corners,dtype=np.float64)
        rotation=np.array(transform.to_3x3(),dtype=np.float64)
        translation=np.array(transform.translation,dtype=np.float64)
        transformed=points @ rotation.T + translation
        lo=Vector(transformed.min(axis=0)); hi=Vector(transformed.max(axis=0))
        if target['min'] is None:
            target['min']=lo; target['max']=hi
        else:
            target['min']=Vector(tuple(min(target['min'][k],lo[k]) for k in range(3)))
            target['max']=Vector(tuple(max(target['max'][k],hi[k]) for k in range(3)))
    return [v for v in targets.values() if v['min'] is not None]

def scene_length(raw_length, scene):
    units=scene.unit_settings
    if units.system=='NONE':
        return raw_length,'BU'
    meters=raw_length*units.scale_length
    name=units.length_unit
    table={'MICROMETERS':(1e-6,'μm'),'MILLIMETERS':(0.001,'mm'),
           'CENTIMETERS':(0.01,'cm'),'METERS':(1.0,'m'),'KILOMETERS':(1000.0,'km'),
           'THOU':(0.0000254,'thou'),'INCHES':(0.0254,'in'),
           'FEET':(0.3048,'ft'),'MILES':(1609.344,'mi')}
    if name not in table:
        if units.system=='IMPERIAL':
            name='MILES' if abs(meters)>=1609.344 else ('FEET' if abs(meters)>=0.3048 else 'INCHES')
        else:
            name='KILOMETERS' if abs(meters)>=1000 else ('METERS' if abs(meters)>=1 else ('CENTIMETERS' if abs(meters)>=0.01 else 'MILLIMETERS'))
    factor,label=table[name]
    return meters/factor,label

def draw_selected_dimensions():
    if not state['enabled']:
        return
    ctx=bpy.context
    if not ctx.region or not ctx.region_data or not ctx.space_data.overlay.show_overlays:
        return
    try:
        shader=gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        segments=[]
        def line(a,b,color):
            segments.extend((tuple(a),tuple(b)))
        signature=(ctx.window_manager.sd_axis_space,tuple((o.as_pointer(),tuple(v for row in o.matrix_world for v in row)) for o in ctx.selected_objects))
        now=time.monotonic()
        if signature != state['signature'] or (state['dirty'] and now-state['last_update']>ctx.window_manager.sd_refresh):
            state['cache']=collect_selected_bounds(ctx)
            state['signature']=signature
            state['dirty']=False
            state['last_update']=now
        measurements=[]
        for target in state['cache']:
            obj=target['object']; lo=target['min']; hi=target['max']; mat=target['matrix']
            edges=[('X',Vector((lo.x,lo.y,hi.z)),Vector((hi.x,lo.y,hi.z))),
                   ('Y',Vector((hi.x,lo.y,hi.z)),Vector((hi.x,hi.y,hi.z))),
                   ('Z',Vector((hi.x,lo.y,lo.z)),Vector((hi.x,lo.y,hi.z)))]
            lengths=[]
            for axis,a,b in edges:
                length=(mat.to_3x3() @ (b-a)).length*ctx.scene.unit_settings.scale_length*1000.0
                lengths.append(length)
                pa=location_3d_to_region_2d(ctx.region,ctx.region_data,mat @ a)
                pb=location_3d_to_region_2d(ctx.region,ctx.region_data,mat @ b)
                if pa is None or pb is None:
                    continue
                d=pb-pa
                if d.length<2:
                    continue
                if max(pa.x,pb.x)<0 or min(pa.x,pb.x)>ctx.region.width or max(pa.y,pb.y)<0 or min(pa.y,pb.y)>ctx.region.height:
                    continue
                direction=d.normalized(); normal=Vector((-direction.y,direction.x))
                for step in range(0,min(int(d.length),20000),9):
                    line(pa+direction*step,pa+direction*min(step+5,d.length),(0.95,0.95,0.95,0.95))
                for p in (pa,pb): line(p-normal*5,p+normal*5,(1,1,1,1))
                if segments:
                    shader.bind(); shader.uniform_float('color',(0.95,0.95,0.95,0.95))
                    batch_for_shader(shader,'LINES',{'pos':segments}).draw(shader)
                    segments.clear()
                raw_length=(mat.to_3x3() @ (b-a)).length
                display_value,unit_label=scene_length(raw_length,ctx.scene)
                value=format(display_value, f'.{ctx.window_manager.sd_decimals}f')
                text=f'{axis}: {value} {unit_label}'
                blf.size(0,ctx.window_manager.sd_font_size); width,height=blf.dimensions(0,text)
                center=(pa+pb)*0.5; x,y=center.x-width/2,center.y-height/2
                x0,y0,x1,y1=x-6,y-5,x+width+6,y+height+5
                shader.bind(); shader.uniform_float('color',(0.035,0.035,0.035,0.82))
                batch_for_shader(shader,'TRIS',{'pos':[(x0,y0),(x1,y0),(x1,y1),(x0,y0),(x1,y1),(x0,y1)]}).draw(shader)
                blf.position(0,x,y,0); blf.color(0,1,1,1,1); blf.draw(0,text)
            measurements.append({'object':obj.name,'mm':lengths})
        state.update(error=None,measurements=measurements)
    except Exception as ex:
        state['error']=repr(ex)
    finally:
        gpu.state.blend_set('NONE')


class SD_OT_show(bpy.types.Operator):
    bl_idname='view3d.selected_dimensions_show'
    bl_label='Show Dimensions'
    bl_description='Measure selected objects; measure each collection instance as a whole'
    def execute(self,context):
        start()
        return {'FINISHED'}

class SD_OT_hide(bpy.types.Operator):
    bl_idname='view3d.selected_dimensions_hide'
    bl_label='Hide Dimensions'
    def execute(self,context):
        stop()
        return {'FINISHED'}

class SD_PT_panel(bpy.types.Panel):
    bl_label='Selected Dimensions'
    bl_idname='SD_PT_selected_dimensions'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='Dimensions'
    def draw(self,context):
        layout=self.layout
        row=layout.row(align=True)
        row.operator('view3d.selected_dimensions_show',icon='HIDE_OFF',depress=state['enabled'])
        row.operator('view3d.selected_dimensions_hide',icon='HIDE_ON')
        layout.prop(context.window_manager,'sd_axis_space',expand=True)
        layout.label(text='X Length · Y Width · Z Height')
        layout.label(text='Units: Follow Scene Settings',icon='SCENE_DATA')
        layout.label(text='Selection only; collection instances supported')
        layout.prop(context.window_manager,'sd_font_size')
        layout.prop(context.window_manager,'sd_decimals')
        layout.prop(context.window_manager,'sd_refresh')
        layout.label(text='Measured along world axes' if context.window_manager.sd_axis_space=='WORLD' else 'Measured along local axes',icon='INFO')
        if state['enabled'] and not context.selected_objects:
            layout.label(text='Select an object to measure')
        if state.get('error'):
            layout.label(text='Annotation error; hide and show dimensions to retry',icon='ERROR')

classes=(SD_OT_show,SD_OT_hide,SD_PT_panel)
def register():
    bpy.app.translations.register(__name__,TRANSLATIONS)
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.WindowManager.sd_axis_space=bpy.props.EnumProperty(name='Coordinate Space',items=[('LOCAL','Local','Measure along the object local X, Y and Z axes'),('WORLD','World','Measure the bounding box along the world X, Y and Z axes')],default='WORLD')
    bpy.types.WindowManager.sd_font_size=bpy.props.IntProperty(name='Font Size',default=17,min=10,max=40)
    bpy.types.WindowManager.sd_decimals=bpy.props.IntProperty(name='Decimal Places',default=2,min=0,max=4)
    bpy.types.WindowManager.sd_refresh=bpy.props.FloatProperty(name='Update Interval (s)',description='Recalculate only when geometry changes; increase for complex scenes',default=0.25,min=0.1,max=3.0)
    if before_load not in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.append(before_load)

def unregister():
    stop()
    bpy.app.translations.unregister(__name__)
    if before_load in bpy.app.handlers.load_pre: bpy.app.handlers.load_pre.remove(before_load)
    for name in ('sd_axis_space','sd_font_size','sd_decimals','sd_refresh'):
        if hasattr(bpy.types.WindowManager,name): delattr(bpy.types.WindowManager,name)
    for cls in reversed(classes): bpy.utils.unregister_class(cls)

if __name__=='__main__': register()
