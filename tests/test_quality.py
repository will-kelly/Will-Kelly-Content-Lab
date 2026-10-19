import unittest, datetime
from wkquality.core import inspect, validate_ledger
class QualityTests(unittest.TestCase):
    def check(self,s):return inspect(s,asof=datetime.date(2026,10,19))['findings']
    def test_unsupported_claim(self):
        self.assertTrue(any(f['tool']=='claim-sentinel' for f in self.check('# Test\n\nResults improved 45% across all teams.')))
    def test_sourced_claim(self):
        self.assertFalse(any(f['tool']=='claim-sentinel' for f in self.check('# Test\n\nAccording to research from a study by Acme, results improved 45%.')))
    def test_code_ignored(self):
        self.assertFalse(any(f['tool']=='jargon-tax' for f in self.check('# Test\n\n```python\nleverage = 2\n```')))
    def test_headings(self):
        self.assertTrue(any(f['rule']=='heading_jump' for f in self.check('# Test\n\n### Deep heading\n')))
    def test_alt(self):
        self.assertTrue(any(f['rule']=='empty_image_alt' for f in self.check('# Test\n\n![](diagram.png)')))
    def test_operational_controls(self):
        self.assertFalse(any(f['tool']=='ai-theater' for f in self.check('# Test\n\nAn agentic workflow has an owner, rollback, evaluation, and review.')))
    def test_ledger(self):
        self.assertTrue(validate_ledger([{'id':'a','claim':'hello','status':'verified','source_url':'','owner':'x','reviewed_on':'2026-10-19'}]))
        self.assertFalse(validate_ledger([{'id':'a','claim':'hello','status':'verified','source_url':'https://example.org','owner':'x','reviewed_on':'2026-10-19'}]))
if __name__=='__main__':unittest.main()
