# -*- coding: utf-8 -*-
"""Odpływy liniowe Harmony z bryły Schedline 2025 „Regular Flow 3D.obj” (Blender, tryb wsadowy).

Bryła wzorcowa: długość nominalna 700 mm, syfon pośrodku z wylotem bocznym, 4 nóżki.
Wg rysunków technicznych LM (assets/img/rys/ec-harmony-*):
  Harmony, Harmony Black       — syfon 100 mm od końca odpływu, wylot boczny (szary syfon);
  Harmony Prime, Prime Black   — syfon pośrodku, wylot wzdłuż odpływu (biały syfon).
Długość 600/700/800/900: środek wydłużany/skracany, końcówki i nóżki przesuwane (nie rozciągane).
Wykończenie: stal szczotkowana/chrom albo czarny mat (ruszt, korpus, kołnierz); nóżki białe.
Uruchom: blender -b --factory-startup --python 10d_blender_odplyw.py -- zadania.json wynik.json
zadania: {klucz: {obj, glb, objout, L (mm), prime (bool), black (bool)}}
"""
import json, math, sys
import bpy, bmesh, mathutils
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
jobs = json.load(open(args[0], encoding='utf-8'))
res = {}


def mat(name, rgb, rough, metal):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m


def bb(o):
    xs = [v.co for v in o.data.vertices]
    return Vector([min(v[i] for v in xs) for i in range(3)]), Vector([max(v[i] for v in xs) for i in range(3)])


for key, J in jobs.items():
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=J['obj'], forward_axis='Y', up_axis='Z')
        bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        o0 = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
        bpy.context.view_layer.objects.active = o0
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        info = {o: bb(o) for o in objs}
        size = {o: (b - a) for o, (a, b) in info.items()}
        # role części (wymiary w mm, oś x = długość)
        body = max(objs, key=lambda o: size[o].x * size[o].y)                       # korpus z kołnierzem
        syf = [o for o in objs if abs((info[o][0].x + info[o][1].x) / 2) < 80 and info[o][1].z < 0 and size[o].x < 130]
        grate = [o for o in objs if o is not body and size[o].x > 600]                 # ruszt
        caps = [o for o in objs if o not in syf and o not in grate and o is not body and size[o].x < 30 and size[o].y > 120]
        legs = [o for o in objs if o not in syf and o not in grate and o not in caps and o is not body]
        L = float(J['L']); d = (L - 700.0) / 2
        # 1. długość: przesunięcie wierzchołków za płaszczyzną cięcia (|x| > 150) i całych końcówek/nóżek
        for o in [body] + grate:
            for v in o.data.vertices:
                if v.co.x > 150: v.co.x += d
                elif v.co.x < -150: v.co.x -= d
        for o in caps + legs:
            a, b = info[o]; s = 1 if (a.x + b.x) > 0 else -1
            o.data.transform(Matrix.Translation((s * d, 0, 0)))
        # 2. syfon
        log = []
        if not J['prime']:
            xs = L / 2 - 100.0                                    # 100 mm od końca odpływu (rysunek Harmony)
            # zalep otwór pod syfon w dnie korpusu w starym miejscu
            bm = bmesh.new(); bm.from_mesh(body.data)
            kill = [f for f in bm.faces if (f.calc_center_median().xy.length < 42 and f.calc_center_median().z < -2)]
            kv = set(v for f in kill for v in f.verts)
            bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
            for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
            bnd = [e for e in bm.edges if len(e.link_faces) == 1 and e.verts[0] in kv and e.verts[1] in kv]
            r = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
            bmesh.ops.triangulate(bm, faces=r['faces'])
            bm.to_mesh(body.data); bm.free()
            log.append('syfon x=%.0f mm, wylot boczny' % xs)
        else:
            xs = 0.0
            log.append('syfon pośrodku, wylot wzdłuż')
        # syfon z Regular Flow nie odpowiada kształtem Harmony -> usunięty, nowy wg packshotów i rysunków LM
        for o in syf:
            bpy.data.objects.remove(o, do_unlink=True)
        objs = [o for o in objs if o not in syf]
        zb = info[body][0].z                                       # spód korpusu odpływu
        def cyl(name, r1, r2, length, loc, axis, seg=48):
            """Walec/stożek: oś 'z' (pionowo, długość w dół od loc), 'x' lub 'y' (poziomo, od loc w + kierunku)."""
            bm = bmesh.new()
            if axis == 'z':
                M = Matrix.Translation((loc[0], loc[1], loc[2] - length / 2))
            elif axis == 'x':
                M = Matrix.Translation((loc[0] + length / 2, loc[1], loc[2])) @ Matrix.Rotation(math.radians(90), 4, 'Y')
            else:
                M = Matrix.Translation((loc[0], loc[1] + length / 2, loc[2])) @ Matrix.Rotation(math.radians(-90), 4, 'X')
            bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=length, matrix=M)
            me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
            return ob
        nsy, nrura = [], []
        if not J['prime']:
            # Harmony: płaski, okrągły korpus pod końcem odpływu + prosta rura Ø50 w bok (poza kołnierz)
            nsy += [cyl('syfon_kolnierz', 44, 44, 2.5, (xs, 0, zb), 'z'),
                    cyl('syfon_korpus', 55, 55, 27, (xs, 0, zb - 2.5), 'z'),
                    cyl('syfon_dno', 55, 44, 7, (xs, 0, zb - 29.5), 'z')]
            nrura += [cyl('syfon_wylot', 25, 25, 118, (xs, -118, zb - 22), 'y'),          # wylot do przodu (jak na packshocie)
                      cyl('syfon_wylot_kielich', 26.5, 26.5, 10, (xs, -118, zb - 22), 'y')]
        else:
            # Prime: korpus pośrodku, rura wzdłuż odpływu z nakrętką złączki i kielichem na końcu
            nsy += [cyl('syfon_kolnierz', 46, 46, 2.5, (xs, 0, zb), 'z'),
                    cyl('syfon_korpus', 40, 40, 30, (xs, 0, zb - 2.5), 'z'),
                    cyl('syfon_dno', 40, 30, 6, (xs, 0, zb - 32.5), 'z'),
                    cyl('syfon_rura', 21, 21, 165, (xs, 0, zb - 26), 'x'),
                    cyl('syfon_nakretka', 29, 29, 24, (xs + 48, 0, zb - 26), 'x', seg=24),
                    cyl('syfon_kielich', 29, 29, 50, (xs + 165, 0, zb - 26), 'x'),
                    cyl('syfon_kielich_wylot', 29, 25, 6, (xs + 215, 0, zb - 26), 'x')]
        # 3. materiały
        ms = mat('czern', (0.025, 0.025, 0.027), 0.45, 0.35) if J['black'] else mat('metal', (0.84, 0.85, 0.86), 0.3, 0.55)   # stal szczotkowana — jasna w każdym oświetleniu
        msy = mat('syfon', (0.92, 0.92, 0.91), 0.45, 0.0) if J['prime'] else mat('syfon', (0.27, 0.28, 0.29), 0.5, 0.0)
        mru = mat('syfon_rura', (0.66, 0.67, 0.68), 0.45, 0.0)
        mn = mat('plastik', (0.93, 0.93, 0.92), 0.5, 0.0)
        msr = mat('sruba', (0.55, 0.56, 0.58), 0.4, 0.6)
        for o in objs:
            o.data.materials.clear()
            if o is body or o in grate or o in caps: o.data.materials.append(ms)
            elif size[o].z > 40 and size[o].x < 15: o.data.materials.append(msr)            # gwintowane trzpienie nóżek
            else: o.data.materials.append(mn)
        for o in nsy: o.data.materials.append(msy)
        for o in nrura: o.data.materials.append(mru)
        objs = objs + nsy + nrura
        for o in objs:
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
            except Exception: pass
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        # 4. pozycja: środek długości w 0, spód w z = 0; mm -> cm (OBJ) -> m (GLB)
        mn3 = Vector((1e9,) * 3); mx3 = -mn3
        for o in objs:
            a, b = bb(o); mn3 = Vector(map(min, mn3, a)); mx3 = Vector(map(max, mx3, b))
        c = (mn3 + mx3) / 2
        for o in objs:
            o.data.transform(Matrix.Translation((-c.x, -c.y, -mn3.z)))
            o.data.transform(Matrix.Diagonal((0.1, 0.1, 0.1, 1)))
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.wm.obj_export(filepath=J['objout'], export_selected_objects=False, export_materials=False, export_uv=False)
        for o in objs:
            o.data.transform(Matrix.Diagonal((0.01, 0.01, 0.01, 1)))
            bmu = bmesh.new(); bmu.from_mesh(o.data); uv = bmu.loops.layers.uv.verify()
            for f in bmu.faces:
                n = f.normal; ax = max(range(3), key=lambda i: abs(n[i])); u, v = [i for i in range(3) if i != ax]
                for l in f.loops: l[uv].uv = (l.vert.co[u] / 0.3, l.vert.co[v] / 0.3)
            bmu.to_mesh(o.data); bmu.free()
        bpy.ops.export_scene.gltf(filepath=J['glb'], export_format='GLB', export_draco_mesh_compression_enable=True, export_yup=True, export_apply=True)
        res[key] = {'dims_mm': [round(x, 1) for x in (mx3 - mn3)], 'log': log,
                    'parts': {'syfon': len(syf), 'ruszt': len(grate), 'koncowki': len(caps), 'nozki': len(legs)}}
    except Exception as e:
        import traceback
        res[key] = {'err': repr(e), 'tb': traceback.format_exc()[-500:]}
json.dump(res, open(args[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
