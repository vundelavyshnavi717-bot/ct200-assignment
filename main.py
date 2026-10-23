import json, hashlib, difflib, uuid
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from .db import SessionLocal, init_db
from .models import Document, DocumentVersion, Node, Selection, SelectionItem, Generation
from .parser import extract_pdf, flatten, content_hash
from .schemas import *
from .generator import generate

app = FastAPI(title='CT-200 QA Traceability API', version='1.0.0')
@app.on_event('startup')
def startup(): init_db()
def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

def node_json(n): return {'id':n.id,'heading':n.heading,'level':n.level,'body_text':n.body_text,'content_hash':n.content_hash,'version_id':n.version_id,'children':[node_json(c) for c in sorted(n.children,key=lambda x:x.ordinal)]}

def latest_version(s, doc_id=1): return s.query(DocumentVersion).filter_by(document_id=doc_id).order_by(desc(DocumentVersion.version_number)).first()

@app.post('/documents/ingest', response_model=IngestResponse)
def ingest(path: str, s: Session=Depends(db)):
    p=Path(path)
    if not p.exists(): raise HTTPException(400, 'PDF path does not exist')
    doc=s.query(Document).filter_by(name='CT-200').first()
    if not doc: doc=Document(name='CT-200'); s.add(doc); s.flush()
    version_no=(s.query(DocumentVersion).filter_by(document_id=doc.id).count()+1)
    version=DocumentVersion(document_id=doc.id, version_number=version_no, source_name=p.name); s.add(version); s.flush()
    roots=extract_pdf(str(p)); count=0; node_by_key={}
    for key, parsed in flatten(roots):
        parent_key=key.rsplit('/',1)[0] if '/' in key else None
        parent=node_by_key.get(parent_key)
        body='\n'.join(parsed.body)
        n=Node(logical_key=key,version_id=version.id,parent_id=parent.id if parent else None,heading=parsed.heading,level=parsed.level,ordinal=count,body_text=body,content_hash=content_hash(parsed.heading,parsed.body),node_type=parsed.node_type)
        s.add(n); s.flush(); node_by_key[key]=n; count+=1
    s.commit(); return IngestResponse(document_id=doc.id,version_id=version.id,version=version_no,node_count=count)

@app.get('/documents/sections')
def sections(version: int|None=None, s: Session=Depends(db)):
    v=latest_version(s) if version is None else s.query(DocumentVersion).filter_by(document_id=1,version_number=version).first()
    if not v: raise HTTPException(404,'Version not found')
    return [node_json(n) for n in s.query(Node).filter_by(version_id=v.id,parent_id=None).order_by(Node.ordinal)]

@app.get('/nodes/{node_id}')
def get_node(node_id:int,s:Session=Depends(db)):
    n=s.get(Node,node_id)
    if not n: raise HTTPException(404,'Node not found')
    return node_json(n)

@app.get('/search', response_model=list[SearchOut])
def search(q:str=Query(min_length=1),version:int|None=None,s:Session=Depends(db)):
    v=latest_version(s) if version is None else s.query(DocumentVersion).filter_by(document_id=1,version_number=version).first()
    if not v: raise HTTPException(404,'Version not found')
    rows=s.query(Node).filter(Node.version_id==v.id,or_(Node.heading.ilike(f'%{q}%'),Node.body_text.ilike(f'%{q}%'))).all()
    return rows

@app.get('/nodes/{node_id}/compare')
def compare(node_id:int, against_version:int|None=None,s:Session=Depends(db)):
    n=s.get(Node,node_id)
    if not n: raise HTTPException(404,'Node not found')
    current=s.query(DocumentVersion).filter_by(id=n.version_id).one(); target=s.query(DocumentVersion).filter_by(document_id=current.document_id,version_number=against_version).first() if against_version else latest_version(s,current.document_id)
    other=s.query(Node).filter_by(version_id=target.id,logical_key=n.logical_key).first()
    if not other: return {'changed':True,'reason':'node missing in comparison version','diff':None}
    changed=n.content_hash!=other.content_hash
    return {'changed':changed,'from_version':current.version_number,'to_version':target.version_number,'diff':list(difflib.unified_diff(n.body_text.splitlines(),other.body_text.splitlines(),lineterm='')) if changed else []}

@app.post('/selections')
def create_selection(payload:SelectionIn,s:Session=Depends(db)):
    nodes=[s.get(Node,i) for i in payload.node_ids]
    if any(n is None for n in nodes): raise HTTPException(400,'Every node ID must exist')
    sel=Selection(name=payload.name); s.add(sel); s.flush()
    for n in nodes: s.add(SelectionItem(selection_id=sel.id,node_id=n.id,version_id=n.version_id,content_hash=n.content_hash))
    s.commit(); return {'id':sel.id,'name':sel.name,'items':[{'node_id':n.id,'version_id':n.version_id,'content_hash':n.content_hash} for n in nodes]}

def selection_text(s,sel):
    items=s.query(SelectionItem).filter_by(selection_id=sel.id).all(); ns=[s.get(Node,i.node_id) for i in items]
    return '\n\n'.join(f'{n.heading}\n{n.body_text}' for n in ns),items

@app.post('/generations', response_model=GenerationOut)
def create_generation(payload:GenerationIn,s:Session=Depends(db)):
    sel=s.get(Selection,payload.selection_id)
    if not sel: raise HTTPException(404,'Selection not found')
    text,items=selection_text(s,sel); snapshot=json.dumps([{'node_id':i.node_id,'version_id':i.version_id,'hash':i.content_hash} for i in items],sort_keys=True)
    # Idempotency policy: identical selection snapshot returns the existing generation.
    existing=s.query(Generation).filter_by(selection_id=sel.id,input_snapshot=snapshot,prompt_version='v1').first()
    if existing: return generation_response(s,existing)
    gid=str(uuid.uuid4()); out=generate(text,[i.node_id for i in items]); g=Generation(id=gid,selection_id=sel.id,input_snapshot=snapshot,output_json=json.dumps(out)); s.add(g); s.commit(); return generation_response(s,g)

def generation_response(s,g):
    stale_reasons=[]; sel=s.get(Selection,g.selection_id)
    for item in s.query(SelectionItem).filter_by(selection_id=sel.id):
        latest=s.query(Node).filter(Node.logical_key==s.get(Node,item.node_id).logical_key,Node.version_id==latest_version(s).id).first()
        if not latest: stale_reasons.append(f'node {item.node_id} is absent from latest version')
        elif latest.content_hash!=item.content_hash: stale_reasons.append(f'node {item.node_id} content changed')
    stale=bool(stale_reasons); g.stale=stale; s.commit()
    return {'id':g.id,'status':g.status,'stale':stale,'stale_reasons':stale_reasons,'test_cases':json.loads(g.output_json)}

@app.get('/generations/{generation_id}', response_model=GenerationOut)
def get_generation(generation_id:str,s:Session=Depends(db)):
    g=s.get(Generation,generation_id)
    if not g: raise HTTPException(404,'Generation not found')
    return generation_response(s,g)

@app.get('/generations')
def list_generations(selection_id:int|None=None,node_id:int|None=None,s:Session=Depends(db)):
    q=s.query(Generation)
    if selection_id: q=q.filter_by(selection_id=selection_id)
    rows=q.all()
    if node_id: rows=[g for g in rows if any(x['node_id']==node_id for x in json.loads(g.input_snapshot))]
    return [generation_response(s,g) for g in rows]
