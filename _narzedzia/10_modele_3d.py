# -*- coding: utf-8 -*-
"""Baza modeli 3D dla LM (pilot): paczka „materiały/008 Modele 3D” (katalog Schedpol 2021) -> indeksy LM.
Krok 1 (python): mapowanie indeks LM -> plik modelu, kopia DWG/OBJ/3DS pod nazwami LM do assets/cad/.
Krok 2 (blender, ten sam plik uruchomiony przez Blendera): pomiar bryły, eksport GLB do podglądu 3D w przeglądarce.
Uruchom:  python 10_modele_3d.py           (mapowanie + kopie + wywołanie Blendera + assets/modele3d.js)
"""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(ROOT), 'materiały', '008 Modele 3D', '01. 3D_SCHEDPOL_2021')
OUT = os.path.join(ROOT, 'assets', 'cad')
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'

# indeks LM -> (folder serii, nazwa pliku bez rozszerzenia). Źródło dopasowania: nazwy z eksportu LM (26.03.2026),
# np. „LDD BRODZIK GRAWELLO KW 80X80X26/12”, „PANEL DANTE 1/4K 80”.
MAP = {
    '42303254': ('13. GRAWELLO', '80x80x26'),       '42303303': ('13. GRAWELLO', '90x90x26'),
    '42303324': ('13. GRAWELLO', '80x80x26 R55'),   '42303331': ('13. GRAWELLO', '90x90x26 R55'),
    '44167333': ('13. GRAWELLO', '80x100x26'),      '44167361': ('13. GRAWELLO', '90x120x26'),
    '43456833': ('15. DANTE', '80x80x41'),          '43456840': ('15. DANTE', '90x90x41'),
    '42960330': ('15. DANTE', '80x80x41 R55'),      '42960442': ('15. DANTE', '90x90x41 R55'),
    '44167375': ('14. GO BABY', '80x80x26 R55'),    '44167382': ('14. GO BABY', '90x90x26 R55'),
    '44516234': ('21. DAFNE', '80x80x35 R55'),      '44516262': ('21. DAFNE', '90x90x35 R55'),
    '42303415': ('24. PANEL GRAWELLO - ZEFIR', '80x80x22,5 R55'), '42303401': ('24. PANEL GRAWELLO - ZEFIR', '90x90x22,5 R55'),
    '43217384': ('27. PANEL DANTE - DORIS', '80x80x37,5 R55'),     '43217391': ('27. PANEL DANTE - DORIS', '90x90x37,5 R55'),
    '44178274': ('25. PANEL GO BABY - BONA', '80x80x26 R55'),      '44178281': ('25. PANEL GO BABY - BONA', '90x90x26 R55'),
    '44516276': ('26. PANEL DAFNE', '80x80x31,5 R55'),             '44516283': ('26. PANEL DAFNE', '90x90x31,5 R55'),
}


def find(folder, stem, exts):
    base = os.path.join(SRC, folder)
    for dp, dn, fn in os.walk(base):
        for f in fn:
            n, e = os.path.splitext(f)
            if n.strip().lower() == stem.lower() and e.lower().lstrip('.') in exts:
                return os.path.join(dp, f)
    return None


def run_blender_part():
    import bpy
    args = sys.argv[sys.argv.index('--') + 1:]
    jobs = json.load(open(args[0], encoding='utf-8'))
    res = {}
    for ref, (obj, glb) in jobs.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=obj)
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if not objs:
            res[ref] = {'err': 'brak siatki'}; continue
        import mathutils
        mn = mathutils.Vector((1e9, 1e9, 1e9)); mx = -mn
        tris = 0
        for o in objs:
            for v in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(v)
                mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
        dims = [round(x, 3) for x in (mx - mn)]
        # materiał: akryl biały, półmat (podgląd; kolor w portalu z danych produktu)
        mat = bpy.data.materials.new('akryl'); mat.use_nodes = True
        b = mat.node_tree.nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value = (0.93, 0.93, 0.92, 1); b.inputs['Roughness'].default_value = 0.45
        for o in objs:
            o.data.materials.clear(); o.data.materials.append(mat)
            bpy.context.view_layer.objects.active = o
        # wyśrodkowanie na podłodze (model-viewer i tak kadruje)
        c = (mn + mx) / 2
        for o in objs:
            o.location -= mathutils.Vector((c.x, c.y, mn.z))
        # OBJ z paczki jest w centymetrach, glTF w metrach -> skala 0,01 (ważne dla AR: model w rzeczywistym rozmiarze)
        for o in objs:
            o.scale = (0.01, 0.01, 0.01); o.location *= 0.01
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        try:
            bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_draco_mesh_compression_enable=True, export_yup=True, export_apply=True)
        except TypeError:
            bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_yup=True, export_apply=True)
        res[ref] = {'dims': dims, 'tris': tris, 'glb_kb': os.path.getsize(glb) // 1024}
    json.dump(res, open(args[1], 'w', encoding='utf-8'), indent=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = json.loads(open(os.path.join(ROOT, 'assets', 'data.js'), encoding='utf-8').read().split('=', 1)[1].split(';\n')[0])
    prods = {p['ref']: p for p in data['products']}
    jobs, files = {}, {}
    for ref, (folder, stem) in MAP.items():
        p = prods[ref]
        brand = p['brand']; fam = p['s'].replace(' ', '-')
        base = '%s_%s_%s_LM%s' % (brand, fam, stem.replace(' ', '-').replace(',', '_'), ref)
        files[ref] = []
        for ext in ('dwg', 'obj', '3ds'):
            src = find(folder, stem, [ext])
            if src:
                dst = os.path.join(OUT, base + '.' + ext)
                shutil.copy2(src, dst)
                files[ref].append({'ext': ext.upper(), 'f': base + '.' + ext, 'kb': os.path.getsize(dst) // 1024})
        obj = find(folder, stem, ['obj'])
        if obj:
            jobs[ref] = (obj, os.path.join(OUT, base + '.glb'))
            files[ref].append({'ext': 'GLB', 'f': base + '.glb', 'kb': 0, 'view': 1})
    jf = os.path.join(OUT, '_jobs.json'); rf = os.path.join(OUT, '_pomiar.json')
    json.dump(jobs, open(jf, 'w', encoding='utf-8'))
    subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.abspath(__file__), '--', jf, rf], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    meas = json.load(open(rf, encoding='utf-8'))
    os.remove(jf); os.remove(rf)
    out = {}
    print('%-9s %-24s %-22s %s' % ('ref', 'model', 'bryła (jednostki pliku)', 'LM a×b×h'))
    for ref, fl in files.items():
        m = meas.get(ref, {})
        for f in fl:
            if f['ext'] == 'GLB':
                f['kb'] = m.get('glb_kb', 0)
        p = prods[ref]
        print('%-9s %-24s %-22s %s×%s×%s' % (ref, MAP[ref][1], m.get('dims'), p.get('a'), p.get('b'), p.get('h')))
        out[ref] = {'src': '2021 · ' + MAP[ref][0].split('. ', 1)[1] + ' · ' + MAP[ref][1], 'dims': m.get('dims'), 'files': fl}
    js = ('/* Modele 3D przypisane do indeksów LM — generuje _narzedzia/10_modele_3d.py z paczki „008 Modele 3D” (katalog Schedpol 2021).\n'
          '   Pilot: Grawello, Dante, Go Baby, Dafne + panele. Pliki w assets/cad/. */\nwindow.SP = window.SP || {};\nwindow.SP.cad = ' +
          json.dumps(out, ensure_ascii=False) + ';\n')
    open(os.path.join(ROOT, 'assets', 'modele3d.js'), 'w', encoding='utf-8').write(js)
    print('modeli:', len(out), ' plików:', sum(len(v['files']) for v in out.values()))


if __name__ == '__main__':
    if '--' in sys.argv and 'bpy' in sys.modules or any('blender' in a.lower() for a in sys.argv[:1]):
        run_blender_part()
    else:
        try:
            import bpy  # noqa: F401
            run_blender_part()
        except ImportError:
            main()
