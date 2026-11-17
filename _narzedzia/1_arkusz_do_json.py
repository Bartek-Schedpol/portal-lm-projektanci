import openpyxl, sys, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = sys.argv[1]
wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
ws = wb["Sheet1"]
rows = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0: 
        print("HEADER:", row[:8]); continue
    if not row or row[0] is None: continue
    rows.append({"ref": str(row[0]).strip(), "seria": (row[1] or "").strip(), "old": (row[2] or "").strip(), "new": (row[3] or "").strip(), "extra": [str(c) for c in row[4:10] if c is not None]})
json.dump(rows, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
c = collections.Counter(r["seria"] for r in rows)
print("ROWS", len(rows))
for k, v in c.most_common(): print(f"  {k!r}: {v}")
print("--- próbka tytułów (po 2 z serii) ---")
seen = collections.Counter()
for r in rows:
    if seen[r["seria"]] < 2:
        seen[r["seria"]] += 1
        print(f'{r["ref"]} | {r["seria"]} | {r["new"]} {r["extra"] if r["extra"] else ""}')
