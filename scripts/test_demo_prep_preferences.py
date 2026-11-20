#!/usr/bin/env python3
"""Local-only demo prep preferences never grant external calendar authority."""
import json
from pathlib import Path
import sys
import unittest
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import onboarding
class DemoPrepPreferences(unittest.TestCase):
 def setUp(self):self.profile=json.loads((ROOT/'profile.example.json').read_text())
 def test_new_users_have_no_outside_world_grants(self):
  self.assertFalse(self.profile['preferences']['demo_prep_booking']['enabled'])
  self.assertTrue(all(value is False for value in self.profile['permissions'].values()))
  self.assertEqual(self.profile['write_authorizations'],[])
 def test_opt_in_is_persistent_preference_not_calendar_authority(self):
  before=deepcopy(self.profile)
  result=onboarding.update(self.profile,{'action':'demo_prep_preferences','enabled':True})
  self.assertTrue(result['preferences']['demo_prep_booking']['enabled'])
  self.assertEqual(result['preferences']['demo_prep_booking']['state'],'requested')
  for key in ['permissions','write_authorizations','schedules','identity','sources']:
   self.assertEqual(result[key],before[key])
  self.assertEqual(self.profile,before)
  off=onboarding.update(result,{'action':'demo_prep_preferences','enabled':False})
  self.assertFalse(off['preferences']['demo_prep_booking']['enabled'])
  self.assertEqual(off['permissions'],before['permissions'])
 def test_permission_imports_and_non_boolean_choices_are_rejected(self):
  for body in [{'enabled':'true'},{'enabled':True,'calendar_writes':True},{'enabled':True,'write_authorizations':['all']}]:
   with self.assertRaises(ValueError):onboarding.update(self.profile,{'action':'demo_prep_preferences',**body})
 def test_saved_user_placement_preferences_survive_toggle(self):
  self.profile['preferences']['demo_prep_booking'].update(minimum_notice_hours=36,prefer_adjacent=True,calendar_color_name='Custom user choice')
  result=onboarding.update(self.profile,{'action':'demo_prep_preferences','enabled':True})
  self.assertEqual(result['preferences']['demo_prep_booking']['minimum_notice_hours'],36)
  self.assertTrue(result['preferences']['demo_prep_booking']['prefer_adjacent'])
  self.assertEqual(result['preferences']['demo_prep_booking']['calendar_color_name'],'Custom user choice')
if __name__=='__main__':unittest.main(verbosity=2)
