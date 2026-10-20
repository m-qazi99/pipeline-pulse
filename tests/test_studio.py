import unittest, sys, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from engine import run

class StudioTests(unittest.TestCase):
 def sample(self):return json.loads((R/'examples/studio.json').read_text())
 def execute(self,**changes):
  p=self.sample();p.update(changes);return run(p)['lab']
 def test_json_serializable(self):json.dumps(run(self.sample()),allow_nan=False)
 def test_fault_propagates(self):
  l=self.execute();s=l['scenario'];self.assertEqual(s['failed'],1);self.assertEqual(s['blocked'],4);self.assertEqual(s['succeeded'],7)
 def test_recovery_restores_every_asset(self):
  l=self.execute();self.assertEqual(l['recovery']['succeeded'],12);self.assertEqual(l['recovery']['blocked'],0)
 def test_retries_resolve_transient_fault(self):
  l=self.execute(failure_count=1,retries=2);self.assertEqual(l['scenario']['succeeded'],12)
 def test_retry_backoff_exact(self):
  from lab import simulate
  n={'a':{'depends':[],'duration':10,'failures':2}};r=simulate(n,['a'],1,2,5)
  self.assertEqual(r['wall_time'],45);self.assertEqual(r['records'][0]['attempts'],3)
 def test_serial_vs_parallel(self):
  a=self.execute(inject='',concurrency=1);b=self.execute(inject='',concurrency=3)
  self.assertGreater(a['scenario']['wall_time'],b['scenario']['wall_time'])
 def test_dependency_start_after_completion(self):
  l=self.execute(inject='');rs={r['id']:r for r in l['scenario']['records']}
  for n in l['nodes']:
   for d in n['depends']:self.assertGreaterEqual(rs[n['id']]['start'],rs[d]['end'])
 def test_cycle_rejected(self):
  with self.assertRaisesRegex(ValueError,'cycle'):self.execute(pipeline=json.dumps([{'id':'a','depends':['b']},{'id':'b','depends':['a']}]),inject='',repair='')
 def test_unknown_dependency_rejected(self):
  with self.assertRaisesRegex(ValueError,'unknown dependency'):self.execute(pipeline='[{"id":"a","depends":["missing"]}]',inject='',repair='')
 def test_duplicate_ids_rejected(self):
  with self.assertRaises(ValueError):self.execute(pipeline='[{"id":"a"},{"id":"a"}]')
 def test_long_blocked_chain(self):
  ns=[{'id':str(i),'depends':[str(i-1)] if i else [],'duration':1} for i in range(15)]
  l=self.execute(pipeline=json.dumps(ns),inject='0',repair='0',retries=0);self.assertEqual(l['scenario']['blocked'],14)
 def test_critical_path_lower_bound(self):
  l=self.execute(inject='');self.assertLessEqual(l['critical_lower_bound'],l['scenario']['wall_time'])
 def test_fractional_worker_count_rejected(self):
  with self.assertRaises(ValueError):self.execute(concurrency=1.5)
 def test_nonfinite_duration_rejected(self):
  with self.assertRaises(ValueError):self.execute(pipeline='[{"id":"a","duration":"NaN"}]',inject='',repair='')
