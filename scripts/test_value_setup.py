import sys,json,unittest,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import onboarding
class ValueSetup(unittest.TestCase):
 def profile(self):return json.loads((ROOT/'profile.example.json').read_text())
 def body(self,**extras):return dict(action='preferences',name='Sample SE',modules={k:True for k in onboarding.MODULES},**extras)
 def test_annual_amount_is_private_local_preference_not_authority(self):
  x=onboarding.update(self.profile(),self.body(role_level='Senior SE',rate_mode='annual',annual_amount=208000,annual_hours=2080,hourly_rate=100,compensation_basis='base'))
  self.assertEqual(x['compensation']['annual_amount'],208000);self.assertFalse(x['identity']['verified']);self.assertFalse(any(x['permissions'].values()));self.assertFalse(x['schedules']['enabled'])
 def test_invalid_financial_inputs_are_rejected(self):
  for key,value in [('annual_hours',0),('hourly_rate',float('nan')),('annual_amount',float('inf'))]:
   with self.subTest(key=key),self.assertRaises(ValueError):onboarding.update(self.profile(),self.body(**{key:value}))
 def test_band_lookup_stays_unverified_without_inventing_a_rate(self):
  x=onboarding.update(self.profile(),self.body(role_level='Senior SE',rate_mode='band'))
  self.assertFalse(x['compensation']['band_verified']);self.assertIsNone(x['compensation']['hourly_rate']);self.assertIn('Role band pending',x['compensation']['basis'])
 def test_location_changes_invalidate_a_previously_verified_band(self):
  p=self.profile();p['organization']['country']='GB';p['compensation'].update(mode='band',currency='GBP',band_verified=True,role_level='Senior')
  x=onboarding.update(p,self.body(role_level='Senior',rate_mode='band',country='US'))
  self.assertFalse(x['compensation']['band_verified']);self.assertEqual(x['compensation']['currency'],'USD')
 def test_shared_defaults_and_code_contain_no_private_pay_catalog(self):
  from compensation import catalog_payload
  profile=self.profile();self.assertIsNone(profile['compensation']['hourly_rate']);self.assertIsNone(profile['compensation']['annual_amount']);self.assertIsNone(profile['compensation']['band_min']);self.assertEqual(catalog_payload(None)['presets'],[])
  self.assertIsNone(profile['identity']['name']);self.assertIsNone(profile['identity']['email'])
  for relative in ['app/compensation.py','app/setup.html','app/onboarding.py']:
   text=(ROOT/relative).read_text();self.assertNotIn('docs.google.com/spreadsheets/d/',text);self.assertIsNone(re.search(r'/(?:Users|home)/[^/\s]+/',text))
 def test_unlisted_country_custom_pay_preserves_actual_profile_country(self):
  x=onboarding.update(self.profile(),self.body(role_key='senior',country='Mexico',currency='MXN',rate_mode='hourly',hourly_rate=800,annual_hours=2080,compensation_basis='ote'))
  self.assertEqual(x['organization']['country'],'Mexico');self.assertEqual(x['compensation']['country'],'OTHER');self.assertEqual(x['compensation']['country_name'],'Mexico');self.assertEqual(x['compensation']['currency'],'MXN');self.assertFalse(x['compensation']['band_verified'])
if __name__=='__main__':unittest.main()
