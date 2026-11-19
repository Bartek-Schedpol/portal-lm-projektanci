import fitz,sys
d=fitz.open('Przegląd oferty (Leroy Merlin) 2025.09a A4.pdf');p=d[27]
def pd(items):
    s=[];last=None
    for it in items:
        if it[0]=='l':
            a,b=it[1],it[2]
            if last is None or abs(last.x-a.x)>.01 or abs(last.y-a.y)>.01: s.append('M%.2f %.2f'%(a.x,a.y))
            s.append('L%.2f %.2f'%(b.x,b.y));last=b
        elif it[0]=='c':
            a,c1,c2,b=it[1:5]
            if last is None or abs(last.x-a.x)>.01 or abs(last.y-a.y)>.01: s.append('M%.2f %.2f'%(a.x,a.y))
            s.append('C%.2f %.2f %.2f %.2f %.2f %.2f'%(c1.x,c1.y,c2.x,c2.y,b.x,b.y));last=b
        elif it[0]=='re':
            r=it[1];s.append('M%.2f %.2f h%.2f v%.2f h%.2f Z'%(r.x0,r.y0,r.width,-0 or r.height,-r.width));last=None
        elif it[0]=='qu':
            q=it[1];s.append('M%.2f %.2f L%.2f %.2f L%.2f %.2f L%.2f %.2f Z'%(q.ul.x,q.ul.y,q.ur.x,q.ur.y,q.lr.x,q.lr.y,q.ll.x,q.ll.y));last=None
    return ' '.join(s)
out=[];bb=None;i=0
for g in p.get_drawings():
    r=g['rect']
    if r.x0>20 and r.x1<230 and r.y0>130 and r.y1<290 and g.get('fill'):
        f=g['fill'];out.append((i,round(f[0],2),pd(g['items'])));i+=1
        bb=r if bb is None else bb|r
print(bb)
for i,f,_ in out: print(i,f)
import json;json.dump({'bb':[bb.x0,bb.y0,bb.x1,bb.y1],'p':out},open(sys.argv[1],'w'))
