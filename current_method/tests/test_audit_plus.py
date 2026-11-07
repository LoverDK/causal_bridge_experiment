import unittest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from atlas_new.core import calibrated_quantile
from atlas_new.audit_plus import assumptions_and_boundaries

class PlusChecks(unittest.TestCase):
    def test_conformal_small_calibration_is_infinite(self):
        self.assertTrue(np.isinf(calibrated_quantile(np.arange(10),.05)))
    def test_boundary_writer_records_returned_infinity(self):
        with patch('atlas_new.audit_plus.save', side_effect=lambda out, name, rows: pd.DataFrame(rows)):
            result = assumptions_and_boundaries({}, Path('.'))
            row = result.set_index('case').loc['small_calibration']
            self.assertEqual(row['observed'], 'infinite')
            self.assertIn('inf', row['detail'])
            with patch('atlas_new.audit_plus.calibrated_quantile', return_value=.25):
                finite = assumptions_and_boundaries({}, Path('.')).set_index('case').loc['small_calibration']
                self.assertEqual(finite['observed'], 'finite')
    def test_plus_protocol_files_exist(self):
        root=Path(__file__).parents[1]
        self.assertTrue((root/'configs'/'full_plus.json').exists())
        self.assertTrue((root/'atlas_new'/'audit_plus.py').exists())
    def test_invalid_r2_is_labelled_in_protocol(self):
        text=(Path(__file__).parents[1]/'docs'/'实验设计与论文对应.md').read_text(encoding='utf-8')
        self.assertIn('adaptive-R2',text)
        self.assertIn('相关',text)

if __name__=='__main__':unittest.main()
