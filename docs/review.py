"""Deterministic review priorities derived from an existing studio result.

No network calls, generated answers, or automatic operational changes.
"""
import json
PROJECT = 'pipeline-pulse'
NAME = 'Pipeline Pulse'

def attach(request, result):
    lab = result['lab']
    items = []

    def add(key, severity, title, detail):
        items.append({'id': key, 'severity': severity, 'title': title, 'detail': detail})
    for r in lab['scenario']['records']:
        if r['status'] == 'failed':
            add('failure-' + r['id'], 'high', r['id'] + ': failed activity', str(r['attempts']) + ' attempt(s), ' + str(r['wait']) + ' seconds of retry backoff. Inspect dependencies and the modeled fault.')
    if lab['scenario']['blocked']:
        add('blocked', 'high', str(lab['scenario']['blocked']) + ' blocked asset(s)', 'Trace the dependency graph to the failed upstream activity. Blocked work is not necessarily a separate cause.')
    recovery = lab['recovery']
    add('recovery', 'review', 'Check recovery coverage before duration', str(recovery['succeeded']) + ' of ' + str(len(lab['nodes'])) + ' activities complete in the repair comparison. It models a change; no real remediation is executed.')
    rec = lab['planner']['recommendation']
    add('capacity', 'info', 'Capacity target comparison', 'Smallest tested worker budget meeting the target: ' + str(rec['workers']) + '.' if rec else 'No tested worker budget completes all work within the target. Review the graph and assumptions.')
    items.sort(key=lambda x: {'high': 0, 'review': 1, 'info': 2}[x['severity']])
    review = {'version': '2.1.0', 'project': PROJECT, 'name': NAME, 'items': items, 'summary': {level: sum((x['severity'] == level for x in items)) for level in ['high', 'review', 'info']}, 'scope': 'Deterministic review aid from this experiment. Checklist completion does not certify correctness, safety, production readiness, or privacy.'}
    report = '# ' + NAME + ' — review handoff\n\n' + review['scope'] + '\n\n'
    for item in items:
        title = item['title'].replace('\n', ' ').replace('\r', ' ')
        detail = item['detail'].replace('\n', ' ').replace('\r', ' ')
        report += '- [ ] [' + item['severity'].upper() + '] ' + title + '\n  ' + detail + '\n'
    result['review'] = review
    result['artifacts'] += [{'name': 'review-handoff.md', 'content': report}, {'name': 'review-priorities.json', 'content': json.dumps(review, indent=2)}]
    return result
