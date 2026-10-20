import unittest,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from engine import run
from challenges import catalog,CASES
class ChallengeTests(unittest.TestCase):
 def request(self,name,**updates):
  c=CASES[name];p={'workspace':'studio','pipeline':json.dumps(c['pipeline']),'inject':'','deadline':c['deadline'],**c['initial'],'challenge':name};p.update(updates);return run(p)['lab']
 def test_all_initial_cases_fail(self):
  for name in CASES:self.assertFalse(self.request(name)['challenge']['passed'])
 def test_bounded_retry_solves_transient(self):self.assertTrue(self.request('transient',retries=1)['challenge']['passed'])
 def test_parallelism_solves_capacity(self):self.assertTrue(self.request('capacity',concurrency=3)['challenge']['passed'])
 def test_causal_repair_solves_schema(self):self.assertTrue(self.request('schema',repair='contract')['challenge']['passed'])
 def test_wrong_repair_does_not_solve_schema(self):self.assertFalse(self.request('schema',repair='dashboard')['challenge']['passed'])
 def test_removing_node_cannot_game_coverage(self):
  ns=CASES['transient']['pipeline'][:1];self.assertFalse(self.request('transient',pipeline=json.dumps(ns),retries=1)['challenge']['passed'])
 def test_shortening_durations_cannot_game_target(self):
  ns=json.loads(json.dumps(CASES['capacity']['pipeline']))
  for n in ns:n['duration']=1
  self.assertFalse(self.request('capacity',pipeline=json.dumps(ns))['challenge']['passed'])
 def test_worker_limit_enforced(self):self.assertFalse(self.request('capacity',concurrency=8)['challenge']['passed'])
 def test_retry_limit_enforced(self):self.assertFalse(self.request('transient',retries=4)['challenge']['passed'])
 def test_unknown_challenge_rejected(self):
  with self.assertRaises(ValueError):self.request('transient',challenge='unknown')
 def test_catalog_copy_is_independent(self):
  a=catalog();a[0]['pipeline'][0]['duration']=999;self.assertEqual(catalog()[0]['pipeline'][0]['duration'],12)
 def test_capacity_frontier_runs_every_budget(self):
  l=self.request('capacity');self.assertEqual(len(l['planner']['policies']),8);self.assertEqual(l['planner']['recommendation']['workers'],3)
 def test_recommendation_infeasible_for_tight_target(self):self.assertIsNone(self.request('capacity',deadline=1)['planner']['recommendation'])
 def test_completion_target_is_validated(self):
  with self.assertRaises(ValueError):self.request('capacity',deadline=0)
 def test_asset_catalog_matches_browser(self):self.assertEqual(json.loads((R/'docs/challenges.json').read_text()),catalog())
