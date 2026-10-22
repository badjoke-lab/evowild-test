import bpy,json
print(json.dumps({'file':bpy.data.filepath,'dirty':bpy.data.is_dirty,'version':bpy.app.version_string,'armatures':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'mcp':hasattr(bpy.types,'blendermcp_server')}))
