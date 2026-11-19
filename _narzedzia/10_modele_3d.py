# -*- coding: utf-8 -*-
"""Baza modeli 3D dla LM z paczki „materiały/008 Modele 3D” (katalog Schedpol 2021).

Serie LM mają w katalogu inne nazwy — rozpoznane po bryle (render vs packshot, wymiary, wysokość, odpływ):
  Balans→KALAIT, Integral→NEW HORIZONS, Magnetic→OMEGA (kamień: OMEGA STONE), Frigo→COMPETIA NEW,
  Ipsilon→CASPAR NEW (kamień: CASPAR NEW STONE), Comfo→GRANDO PLUS, Sinergid→EKO 2, Torres→FERRA;
  Grawello, Dante, Go Baby, Dafne i panele — te same nazwy.
Dopasowanie indeksu LM do pliku: po ZMIERZONYCH wymiarach głównej bryły (nazwy plików w paczce bywają błędne)
i kształcie (R55 = półokrągły, 5k = pięciokątny). Pliki wspólne dla wariantów kolorystycznych (ta sama bryła).

Uruchom:  python 10_modele_3d.py   -> assets/cad/*.dwg|obj|3ds|glb + assets/modele3d.js
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(ROOT), 'materiały', '008 Modele 3D', '01. 3D_SCHEDPOL_2021')
OUT = os.path.join(ROOT, 'assets', 'cad')
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'

SERIES = {  # seria LM -> foldery katalogu (drugi = wersja kamienna)
    'Balans': ['00. KALAIT'], 'Integral': ['09. NEW HORIZONS'], 'Magnetic': ['03. OMEGA', '04. OMEGA STONE'],
    'Frigo': ['11. COMPETIA NEW'], 'Ipsilon': ['17. CASPAR NEW', '18. CASPAR NEW STONE'], 'Comfo': ['12. GRANDO PLUS'],
    'Sinergid': ['19. EKO 2'], 'Torres': ['30. FERRA'],
    'Grawello': ['13. GRAWELLO'], 'Dante': ['15. DANTE'], 'Go Baby': ['14. GO BABY'], 'Dafne': ['21. DAFNE'],
}
PANELS = {'Panel Grawello': '24. PANEL GRAWELLO - ZEFIR', 'Panel Dante': '27. PANEL DANTE - DORIS',
          'Panel Go Baby': '25. PANEL GO BABY - BONA', 'Panel Dafne': '26. PANEL DAFNE'}
H_TOL = 2.0   # cm — tolerancja wysokości (np. Omega 5,5 vs Magnetic 5)


def shape_of_name(f):
    n = f.lower()
    if '5k' in n: return 'pięciokątny'
    if 'r55' in n or 'r90' in n: return 'półokrągły'
    return None


def main_dims(path):
    """Wymiary największej bryły w pliku OBJ (bez dołożonych obok kratek / akcesoriów), posortowane malejąco."""
    verts, faces, cur = [], {}, '_'
    with open(path, encoding='latin-1') as f:
        for l in f:
            if l.startswith('v '):
                verts.append([float(x) for x in l.split()[1:4]])
            elif l[:2] in ('o ', 'g '):
                cur = l.strip()
            elif l.startswith('f '):
                s = faces.setdefault(cur, set())
                for t in l.split()[1:]:
                    i = int(t.split('/')[0]); s.add(i - 1 if i > 0 else len(verts) + i)
    best = None
    for idx in faces.values():
        P = [verts[i] for i in idx]
        d = sorted(max(p[k] for p in P) - min(p[k] for p in P) for k in range(3))
        if best is None or d[1] * d[2] > best[1] * best[2]:
            best = d
    return [round(best[2], 1), round(best[1], 1), round(best[0], 1)] if best else None


def catalog(folder):
    out = []
    for dp, dn, fn in os.walk(os.path.join(SRC, folder)):
        for f in fn:
            if f.lower().endswith('.obj'):
                p = os.path.join(dp, f)
                out.append({'obj': p, 'stem': os.path.splitext(f)[0], 'dims': main_dims(p), 'shape': shape_of_name(f)})
    return out


def sibling(objpath, ext):
    stem = os.path.splitext(os.path.basename(objpath))[0].strip().lower()
    base = os.path.dirname(os.path.dirname(objpath))
    for dp, dn, fn in os.walk(base):
        for f in fn:
            n, e = os.path.splitext(f)
            if n.strip().lower() == stem and e.lower() == '.' + ext:
                return os.path.join(dp, f)
    return None


def run_blender_part():
    import bpy, mathutils
    args = sys.argv[sys.argv.index('--') + 1:]
    jobs = json.load(open(args[0], encoding='utf-8'))
    res = {}
    for key, (obj, glb) in jobs.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=obj)
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if not objs:
            res[key] = {'err': 'brak siatki'}; continue
        # rozdziel na luźne części (kratki leżące obok bywają w tym samym obiekcie co brodzik)
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs[0].data.vertices) < 400000:
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        def bb(o):
            ws = [o.matrix_world @ mathutils.Vector(v) for v in o.bound_box]
            return mathutils.Vector([min(w[i] for w in ws) for i in range(3)]), mathutils.Vector([max(w[i] for w in ws) for i in range(3)])
        # zostaw główną bryłę i to, co w jej obrysie (usuń kratki/akcesoria leżące obok)
        big = max(objs, key=lambda o: (lambda a, b: sorted(b - a)[1] * sorted(b - a)[2])(*bb(o)))
        bmn, bmx = bb(big)
        for o in list(objs):
            a, b = bb(o); c = (a + b) / 2
            if any(c[i] < bmn[i] - 1 or c[i] > bmx[i] + 1 for i in range(3)):
                bpy.data.objects.remove(o, do_unlink=True); objs.remove(o)
        mn = mathutils.Vector((1e9,) * 3); mx = -mn
        for o in objs:
            a, b = bb(o); mn = mathutils.Vector(map(min, mn, a)); mx = mathutils.Vector(map(max, mx, b))
        mat = bpy.data.materials.new('akryl'); mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (0.93, 0.93, 0.92, 1); bsdf.inputs['Roughness'].default_value = 0.45
        for o in objs:
            o.data.materials.clear(); o.data.materials.append(mat)
        c = (mn + mx) / 2
        for o in objs:
            o.location -= mathutils.Vector((c.x, c.y, mn.z))
            o.scale = (0.01, 0.01, 0.01); o.location *= 0.01          # OBJ w cm -> glTF w metrach (AR 1:1)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_draco_mesh_compression_enable=True, export_yup=True, export_apply=True)
        res[key] = {'dims': [round(x, 1) for x in (mx - mn)], 'glb_kb': os.path.getsize(glb) // 1024}
    json.dump(res, open(args[1], 'w', encoding='utf-8'), indent=1)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    data = json.loads(open(os.path.join(ROOT, 'assets', 'data.js'), encoding='utf-8').read().split('=', 1)[1].split(';\n')[0])
    prods = data['products']
    cats = {}
    def cat(folder):
        if folder not in cats: cats[folder] = catalog(folder)
        return cats[folder]

    models, refs, miss = {}, {}, []   # models: klucz pliku -> {obj, ...}; refs: ref -> klucz
    for p in prods:
        if p['fam'] in SERIES and p.get('a') and p.get('b'):
            folders = SERIES[p['fam']]
            stone = 'kamień' in (p.get('c') or '') or 'kamien' in (p.get('c') or '')
            folder = folders[1] if stone and len(folders) > 1 else folders[0]
            want = sorted([float(p['a']), float(p['b'])], reverse=True)
            shp = p.get('shape') if p.get('shape') in ('półokrągły', 'pięciokątny') else None
            try:
                h = float(str(p.get('h') or '0').split('/')[0].replace(',', '.'))
            except ValueError:
                h = 0
            cand = [m for m in cat(folder) if m['dims'] and abs(m['dims'][0] - want[0]) <= 0.6 and abs(m['dims'][1] - want[1]) <= 0.6 and m['shape'] == shp]
            if p['fam'] not in ('Grawello', 'Dante', 'Go Baby', 'Dafne') and h:
                cand = [m for m in cand if abs(m['dims'][2] - h) <= H_TOL]
            if not cand:
                miss.append('%s %s %s %s×%s×%s' % (p['ref'], p['fam'], p.get('shape'), p['a'], p['b'], p.get('h'))); continue
            m = sorted(cand, key=lambda m: abs(m['dims'][2] - h))[0]
        elif p['s'] in PANELS:
            size = '90' if p['ref'] in ('42303401', '43217391', '44178281', '44516283') else '80'
            m = next((m for m in cat(PANELS[p['s']]) if m['stem'].startswith(size)), None)
            if not m:
                miss.append(p['ref'] + ' ' + p['s']); continue
        else:
            continue
        dims = m['dims']
        tag = '-R55' if m['shape'] == 'półokrągły' else ('-5k' if m['shape'] == 'pięciokątny' else '')
        key = '%s_%s_%gx%gx%g%s' % (p['brand'], (p['s'] if p['s'] in PANELS else p['fam']).replace(' ', '-'), dims[0], dims[1], dims[2], tag)
        key = key.replace('.', ',')
        models.setdefault(key, {'obj': m['obj'], 'src': os.path.relpath(m['obj'], SRC).split(os.sep)[0].split('. ', 1)[1] + ' · ' + m['stem'], 'dims': dims, 'refs': []})
        models[key]['refs'].append(p['ref'])
        refs[p['ref']] = key

    jobs = {}
    for key, m in models.items():
        files = []
        for ext in ('dwg', 'obj', '3ds'):
            src = m['obj'] if ext == 'obj' else sibling(m['obj'], ext)
            if src and ext == 'obj':                                  # OBJ to tekst — w ZIP ~6× mniejszy
                import zipfile
                zp = os.path.join(OUT, key + '.obj.zip')
                with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                    z.write(src, key + '.obj')
                files.append({'ext': 'OBJ', 'f': key + '.obj.zip', 'kb': os.path.getsize(zp) // 1024, 'zip': 1})
            elif src:
                shutil.copy2(src, os.path.join(OUT, key + '.' + ext))
                files.append({'ext': ext.upper(), 'f': key + '.' + ext, 'kb': os.path.getsize(src) // 1024})
        files.append({'ext': 'GLB', 'f': key + '.glb', 'kb': 0, 'view': 1})
        m['files'] = files
        jobs[key] = (m['obj'], os.path.join(OUT, key + '.glb'))
    jf = os.path.join(OUT, '_jobs.json'); rf = os.path.join(OUT, '_pomiar.json')
    json.dump(jobs, open(jf, 'w', encoding='utf-8'))
    subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.abspath(__file__), '--', jf, rf], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    meas = json.load(open(rf, encoding='utf-8')); os.remove(jf); os.remove(rf)
    out = {}
    for ref, key in refs.items():
        m = models[key]
        for f in m['files']:
            if f['ext'] == 'GLB':
                f['kb'] = meas.get(key, {}).get('glb_kb', 0)
        out[ref] = {'src': '2021 · ' + m['src'], 'dims': m['dims'], 'files': m['files']}
    js = ('/* Modele 3D przypisane do indeksów LM — generuje _narzedzia/10_modele_3d.py z paczki „008 Modele 3D” (katalog Schedpol 2021).\n'
          '   Serie LM rozpoznane po bryle (nazwy katalogowe inne). Pliki w assets/cad/, wspólne dla wariantów kolorystycznych. */\n'
          'window.SP = window.SP || {};\nwindow.SP.cad = ' + json.dumps(out, ensure_ascii=False) + ';\n')
    open(os.path.join(ROOT, 'assets', 'modele3d.js'), 'w', encoding='utf-8').write(js)
    by = {}
    for ref, key in refs.items():
        fam = next(p['fam'] for p in prods if p['ref'] == ref)
        by[fam] = by.get(fam, 0) + 1
    print('indeksów z modelem:', len(out), ' unikalnych brył:', len(models), ' plików:', len(os.listdir(OUT)))
    print('wg serii:', by)
    print('bez modelu w paczce (%d):' % len(miss))
    for x in miss:
        print('  ', x)


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401
        run_blender_part()
    except ImportError:
        main()
