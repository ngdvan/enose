"""Meaningful leakage, pairing, and tiny-budget regression tests."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from revision_common import split_groups, paired_summary, metrics
from run_major_revision import choose, windows
from revision_drift import split
from generic_ssl import PatchEncoder
import same_device_session_transfer as core


class ProtocolTests(unittest.TestCase):
    def test_exposure_split(self):
        groups=np.repeat(np.arange(5),5)
        tr,va=split_groups(groups,42)
        self.assertFalse(set(groups[tr])&set(groups[va]))
        self.assertEqual(int(va.sum()),5)

    def test_one_label_never_reused(self):
        labels=np.arange(6)
        tr,va=split(np.arange(6),labels,42)
        self.assertEqual(len(tr),6);self.assertEqual(len(va),0)

    def test_pair_design_unique(self):
        core.TARGET_SCALE=np.array([500,500])
        y=np.array([[0,0],[0,0],[50,100],[100,50],[500,500],[250,250]])
        p=dict(ay0=y,ag0=np.arange(6),ag=np.repeat(np.arange(6),5),
               ax=np.zeros((30,64,20)),ay=np.repeat(y,5,axis=0))
        for design in ['random','farthest']:
            x,ys,g,tr,va=choose(p,5,42,design)
            self.assertEqual(len(np.unique(ys,axis=0)),5)
            self.assertFalse(set(g[tr])&set(g[va]))

    def test_bootstrap_known_difference(self):
        rows=[]
        for seed in range(10):
            for fold in range(3):
                for policy,value in [('scratch',5.),('fine_tuned',3.)]:
                    rows.append(dict(dataset='x',fold=fold,seed=seed,budget=5,design='farthest',window='early',
                                     gas='gas',policy=policy,mae=value,n_test=4))
        result=paired_summary(pd.DataFrame(rows),n_boot=100).iloc[0]
        self.assertEqual(result.improvement,2.);self.assertEqual(result.ci_low,2.)
        with self.assertRaises(Exception):
            paired_summary(pd.DataFrame(rows+[rows[0]]),n_boot=10)

    def test_window_definitions(self):
        raw=np.repeat(np.arange(430)[:,None],20,axis=1)
        data=dict(raw=[raw],targets=[[1,2]],groups=[7])
        for pos,start in [('early',0),('middle',181),('late',362)]:
            x,_,_=windows(data,[0],pos)
            self.assertEqual(x.shape,(5,64,20));self.assertEqual(x[0,0,0],start)
        x,_,_=windows(data,[0],'full',False)
        self.assertEqual(x[0,-1,0],429)

    def test_generic_no_channel_identity(self):
        encoder=PatchEncoder().eval()
        x=torch.randn(2,64,3)
        with torch.no_grad():
            a=encoder(x);b=encoder(x[:,:,[2,0,1]])
        torch.testing.assert_close(a[:,[2,0,1]],b)

    def test_constant_target_r2(self):
        self.assertIsNone(metrics(np.ones(3),np.zeros(3),1)['r2'])


if __name__=='__main__': unittest.main()
