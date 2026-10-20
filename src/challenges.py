"""Reproducible incident exercises with explicit, deterministic success criteria."""
from copy import deepcopy

def node(key, duration, depends=(), failures=0):
    return {'id':key, 'label':key.replace('_',' ').title(), 'duration':duration,
            'depends':list(depends), 'failures':failures, 'kind':'activity'}

CASES = {
    'transient': {
        'id':'transient', 'title':'The transient failure', 'level':'01 / Retry strategy',
        'brief':'A storage read fails once before succeeding. Deliver the mart within 80 seconds without changing the graph or repairing a node.',
        'hint':'One failed attempt consumes a full activity duration. A bounded retry can recover this fault; backoff still counts against the target.',
        'deadline':80, 'max_workers':2, 'max_retries':2, 'repair_node':None,
        'pipeline':[node('storage_read',12,failures=1),node('landing',20,['storage_read']),node('quality_gate',8,['landing']),node('sales_mart',12,['quality_gate'])],
        'initial':{'concurrency':2,'retries':0,'backoff':5,'repair':''}},
    'capacity': {
        'id':'capacity', 'title':'The crowded worker pool', 'level':'02 / Capacity planning',
        'brief':'Three independent extracts feed a shared model. Complete the dashboard within 80 seconds using at most four workers. Keep the activity definitions intact.',
        'hint':'The three sources can run concurrently. Follow their dependency boundaries before increasing retries.',
        'deadline':80, 'max_workers':4, 'max_retries':1, 'repair_node':None,
        'pipeline':[node('orders',40),node('customers',40),node('products',40),node('model',20,['orders','customers','products']),node('dashboard',10,['model'])],
        'initial':{'concurrency':1,'retries':0,'backoff':5,'repair':''}},
    'schema': {
        'id':'schema', 'title':'Repair the upstream cause', 'level':'03 / Dependency reasoning',
        'brief':'The contract activity persistently fails. Select the single activity to repair in the recovery comparison, restore every asset, and finish within 100 seconds. At most one retry is allowed.',
        'hint':'A blocked dashboard is a symptom. Repairing a downstream activity does not repair its upstream contract.',
        'deadline':100, 'max_workers':2, 'max_retries':1, 'repair_node':'contract',
        'pipeline':[node('source',10),node('contract',15,['source'],10),node('model',25,['contract']),node('dashboard',8,['model'])],
        'initial':{'concurrency':2,'retries':0,'backoff':5,'repair':''}}
}

def catalog():
    return deepcopy(list(CASES.values()))

def evaluate(case_id, nodes, p, scenario, recovery):
    if case_id not in CASES:
        raise ValueError('Unknown incident challenge.')
    case=CASES[case_id]
    expected={n['id']:n for n in case['pipeline']}
    intact=set(nodes)==set(expected) and all(
        n['duration']==expected[k]['duration'] and
        n['failures']==expected[k]['failures'] and
        sorted(n['depends'])==sorted(expected[k]['depends'])
        for k,n in nodes.items())
    # Global validation has already bounded these values in lab.run.
    guardrails=(int(float(p.get('concurrency',3)))<=case['max_workers'] and
                int(float(p.get('retries',0)))<=case['max_retries'] and not p.get('inject'))
    repair=p.get('repair','')
    correct_repair=(repair==case['repair_node']) if case['repair_node'] else not repair
    observed=recovery if case['repair_node'] else scenario
    checks=[
        {'label':'Original topology and timings preserved','passed':intact},
        {'label':'Within worker, retry, and fault constraints','passed':guardrails},
        {'label':'Correct repair selection','passed':correct_repair},
        {'label':'Every activity completes','passed':observed['succeeded']==len(expected) and not observed['failed'] and not observed['blocked']},
        {'label':f"Completion within {case['deadline']} seconds",'passed':observed['wall_time']<=case['deadline']}
    ]
    return {'id':case_id,'title':case['title'],'passed':all(c['passed'] for c in checks),
            'checks':checks,'completed':observed['succeeded'],'total':len(expected),
            'wall_time':observed['wall_time'],'deadline':case['deadline'],
            'evaluated_run':'recovery' if case['repair_node'] else 'scenario',
            'hint':case['hint']}
