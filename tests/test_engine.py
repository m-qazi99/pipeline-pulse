import unittest,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from engine import run
from common import read_csv
class EngineTests(unittest.TestCase):
 def sample(self):return json.loads((R/'examples/sample.json').read_text())
 def test_empty_csv_rejected(self):
  with self.assertRaises(ValueError):read_csv('')
 def test_duplicate_headers_rejected(self):
  with self.assertRaises(ValueError):read_csv('a,a\n1,2')
 def test_ragged_csv_rejected(self):
  with self.assertRaises(ValueError):read_csv('a,b\n1')
 def test_quoted_csv_and_bom(self):
  h,r=read_csv('\ufeffid,note\n1,"hello, world"');self.assertEqual(r[0]['note'],'hello, world')
 def test_sample_classifications(self):
  r=run(self.sample());self.assertEqual(r['metrics'][1]['value'],3);self.assertIn('Access / authentication',[x[3]for x in r['table']['rows']]);self.assertTrue(r['artifacts'][0]['content'])
 def test_invalid_json(self):
  with self.assertRaises(ValueError):run({'logs':'not json'})
 def test_object_rejected(self):
  with self.assertRaises(ValueError):run({'logs':'{}'})
 def test_negative_duration_rejected(self):
  with self.assertRaises(ValueError):run({'logs':'[{"duration_seconds":-1}]'})
 def test_unknown_failure_does_not_invent_cause(self):
  r=run({'logs':'[{"status":"Failed","error":"unrecognized signal"}]'});self.assertEqual(r['table']['rows'][0][3],'Unclassified failure')
 def test_running_is_not_success(self):
  r=run({'logs':'[{"status":"Running"}]'});self.assertEqual(r['metrics'][2]['value'],'0.0%')

if __name__=='__main__':unittest.main()
