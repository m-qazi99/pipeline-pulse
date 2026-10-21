"""Rule-based pipeline incident triage. Suggestions are explicitly hypotheses."""
import json
from collections import Counter
from common import *
RULES=[(('timeout','timed out'),'Timeout / capacity','Check activity duration, integration-runtime capacity, network latency, and retry policy.'),(('unauthorized','forbidden','403','401','authentication'),'Access / authentication','Check identity, token expiry, role assignments, and storage/database permissions.'),(('schema','column','mapping','type mismatch'),'Schema / mapping','Compare source and sink schemas; review changed columns and conversion rules.'),(('not found','404','pathnotfound'),'Missing resource','Confirm the path, dataset parameters, container, and resource existence.'),(('throttl','429','rate limit'),'Throttling','Review concurrency and provider quotas; consider exponential backoff with jitter.')]

def legacy_run(p):
    raw=p.get('logs','')
    if not isinstance(raw,str) or len(raw)>MAX_CHARS:raise ValueError('Logs must be text under 2 MB.')
    try:events=json.loads(raw)
    except json.JSONDecodeError as e:raise ValueError('Use a JSON array of activity events.')from e
    if not isinstance(events,list) or not events:raise ValueError('Supply a non-empty JSON array.')
    if len(events)>MAX_ROWS:raise ValueError('Use at most 10,000 activity events.')
    output=[];findings=[];groups=Counter();report=['PIPELINE INCIDENT REVIEW','Rule-based hypotheses; validate before remediation.','']
    failed=0;duration=0
    for i,e in enumerate(events):
        if not isinstance(e,dict):raise ValueError(f'Event {i+1} must be a JSON object.')
        status=str(e.get('status','Unknown'));activity=str(e.get('activity',e.get('activityName',f'Activity {i+1}')))
        message=e.get('error',e.get('message',''));message=json.dumps(message,ensure_ascii=False)if isinstance(message,(dict,list))else str(message)
        sec=number(e.get('duration_seconds',0))
        if sec is None or sec<0 or sec>10**9:raise ValueError(f'Event {i+1}: duration_seconds must be a finite, non-negative number below 1 billion.')
        duration+=float(sec);category='Healthy' if status.lower() in {'succeeded','success','completed'}else 'Not assessed'
        if status.lower() in {'failed','error','failure'}:
            failed+=1;category='Unclassified failure';next_step='Inspect full activity output, dependencies, and recent changes.'
            for words,label,action in RULES:
                if any(w in message.lower() for w in words):category=label;next_step=action;break
            findings.append(finding('error',activity+' · '+category,next_step+' Suggested hypothesis, not a confirmed root cause.'))
            report.extend([f'{activity}: {category}',message,next_step,''])
        groups[category]+=1
        output.append([activity,status,f'{float(sec):g}',category,message[:400]])
    if not failed:findings.append(finding('success','No failed events reported','Running, cancelled, and unknown statuses still require review; only explicit failure statuses are classified.'))
    return result('Pipeline review complete',[metric('Activities',len(events)),metric('Failed',failed),metric('Success rate',f'{100*sum(str(e.get("status","")).lower()in {"succeeded","success","completed"}for e in events)/len(events):.1f}%'),metric('Activity seconds',f'{duration:g}','Sum of durations; not wall-clock duration')],['Activity','Status','Seconds','Classification','Error / message'],output,findings,[{'label':k,'value':v}for k,v in groups.items()],[{'name':'incident-review.txt','content':'\n'.join(report)}])


def run(p):
    if not isinstance(p,dict):raise ValueError("Send a JSON object.")
    if p.get("workspace")=="studio":
        from lab import run as studio_run
        from review import attach
        return attach(p, studio_run(p))
    return legacy_run(p)
