"""Discrete-event DAG laboratory: dependency validation, bounded retries and replay."""
import json, heapq, math
from collections import deque
from common import result, metric, finding

def integer(value, name, low, high):
    try:n=float(value)
    except (TypeError, ValueError):raise ValueError(f'{name} must be an integer.')
    if not math.isfinite(n) or n!=int(n) or not low<=n<=high:raise ValueError(f'{name} must be between {low} and {high}.')
    return int(n)

def graph(raw):
    try:ns=json.loads(raw) if isinstance(raw,str) else raw
    except (ValueError,TypeError):raise ValueError('Pipeline must be a JSON array of nodes.')
    if not isinstance(ns,list) or not 1<=len(ns)<=40:raise ValueError('Use 1–40 pipeline nodes.')
    nodes={}
    for n in ns:
        if not isinstance(n,dict):raise ValueError('Each node must be an object.')
        key=n.get('id','')
        if not isinstance(key,str) or not key.strip() or len(key)>60 or key in nodes:raise ValueError('Node IDs must be unique, nonempty text under 60 characters.')
        deps=n.get('depends',[])
        if not isinstance(deps,list) or any(not isinstance(d,str) for d in deps) or len(set(deps))!=len(deps):raise ValueError('Dependencies must be an array of unique node IDs.')
        nodes[key]={'id':key,'label':str(n.get('label',key))[:80],'depends':deps,'duration':integer(n.get('duration',30),'Duration',1,3600),'failures':integer(n.get('failures',0),'Failures',0,10),'kind':str(n.get('kind','transform'))[:30]}
    for key,n in nodes.items():
        if any(d not in nodes for d in n['depends']):raise ValueError(f'{key}: unknown dependency.')
    order=[];pending=dict(nodes);levels={}
    while pending:
        ready=[k for k,n in pending.items() if all(d in levels for d in n['depends'])]
        if not ready:raise ValueError('Dependency cycle detected. A pipeline must be a directed acyclic graph.')
        for k in ready:levels[k]=max((levels[d]+1 for d in nodes[k]['depends']),default=0);order.append(k);del pending[k]
    return nodes,order,levels

def simulate(nodes,order,slots,retries,backoff,repair=None):
    pending=set(order);running=[];finished={};records={};now=0;seq=0
    while pending or running:
        blocked=[k for k in order if k in pending and any(finished.get(d) in {'failed','blocked'} for d in nodes[k]['depends'])]
        for k in blocked:
            records[k]={'id':k,'status':'blocked','start':None,'end':now,'attempts':0,'wait':0};finished[k]='blocked';pending.remove(k)
        ready=[k for k in order if k in pending and all(finished.get(d)=='succeeded' for d in nodes[k]['depends'])]
        for k in ready[:max(0,slots-len(running))]:
            n=nodes[k];fails=0 if k==repair else n['failures'];attempts=min(fails+1,retries+1)
            wait=sum(min(60,backoff*2**i) for i in range(attempts-1));end=now+n['duration']*attempts+wait
            state='succeeded' if fails<=retries else 'failed'
            records[k]={'id':k,'status':state,'start':now,'end':end,'attempts':attempts,'wait':wait}
            heapq.heappush(running,(end,seq,k));seq+=1;pending.remove(k)
        if running:
            now=running[0][0]
            while running and running[0][0]==now:
                _,_,k=heapq.heappop(running);finished[k]=records[k]['status']
        elif pending:
            # Newly blocked nodes propagate through arbitrarily long branches.
            if blocked:continue
            raise ValueError('No schedulable activities remain.')
    ordered=[records[k] for k in order]
    return {'records':ordered,'wall_time':now,'succeeded':sum(r['status']=='succeeded' for r in ordered),'failed':sum(r['status']=='failed' for r in ordered),'blocked':sum(r['status']=='blocked' for r in ordered),'compute_seconds':sum((r['end']-r['start']-r['wait']) for r in ordered if r['start'] is not None)}

def run(p):
    nodes,order,levels=graph(p.get('pipeline',''))
    slots=integer(p.get('concurrency',3),'Concurrency',1,8);retries=integer(p.get('retries',0),'Retries',0,4);backoff=integer(p.get('backoff',5),'Backoff',0,30)
    inject=p.get('inject','')
    if inject:
        if inject not in nodes:raise ValueError('The injected-failure node does not exist.')
        nodes[inject]['failures']=integer(p.get('failure_count',3),'Injected failures',1,10)
    repair=p.get('repair',inject)
    if repair and repair not in nodes:raise ValueError('The recovery node does not exist.')
    primary=simulate(nodes,order,slots,retries,backoff)
    recovered=simulate(nodes,order,slots,retries,backoff,repair)
    earliest={};previous={}
    for k in order:
        deps=nodes[k]['depends'];prev=max(deps,key=lambda x:earliest[x]) if deps else None
        earliest[k]=(earliest[prev] if prev else 0)+nodes[k]['duration'];previous[k]=prev
    end=max(order,key=lambda x:earliest[x]);path=[];cursor=end
    while cursor is not None:path.append(cursor);cursor=previous[cursor]
    path.reverse()
    affected=set()
    if inject:
        q=deque([inject])
        while q:
            n=q.popleft()
            for k in order:
                if n in nodes[k]['depends'] and k not in affected:affected.add(k);q.append(k)
    rows=[[r['id'],r['status'],r['start'] if r['start'] is not None else '—',r['end'],r['attempts'],r['wait']] for r in primary['records']]
    report={'scenario':primary,'recovery':recovered,'critical_path':path,'critical_lower_bound':earliest[end],'blast_radius':sorted(affected),'assumptions':['Deterministic synthetic simulation; no Azure resources are contacted.','Retries hold the worker slot during backoff. Each failed attempt consumes the configured duration.','Critical path is the dependency lower bound with healthy nodes and unlimited concurrency.']}
    out=result('Pipeline simulation complete',[metric('Completed',f"{primary['succeeded']}/{len(nodes)}"),metric('Blocked assets',primary['blocked']),metric('Wall time',f"{primary['wall_time']}s"),metric('Recovery completion',f"{recovered['succeeded']}/{len(nodes)}")],['Activity','Outcome','Start (s)','End (s)','Attempts','Backoff (s)'],rows,[finding('info','Recovery is a comparison, not an executed fix','The comparison removes failures from the selected recovery node. It does not change cloud resources.')],artifacts=[{'name':'pipeline-experiment.json','content':json.dumps(report,indent=2)},{'name':'pipeline-definition.json','content':json.dumps(list(nodes.values()),indent=2)}])
    out['lab']={**report,'nodes':[{**nodes[k],'level':levels[k]} for k in order]};return out
