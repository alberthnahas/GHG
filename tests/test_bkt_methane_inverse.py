import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from bkt_methane_inverse import InverseProblem,chain_diagnostics,correlated_error


class MethaneInverseTests(unittest.TestCase):
    def problem(self):
        rng=np.random.default_rng(8)
        k=rng.uniform(0,100,(40,2))
        b=np.ones((40,1))
        y=k@np.array([1.4,.6])+3
        return InverseProblem(k,b,y,np.eye(40)*4,np.array([1.,1.,20.]))

    def test_exact_synthetic_recovery(self):
        p=self.problem();theta,cov,result=p.fit()
        np.testing.assert_allclose(np.exp(theta[:2]),[1.4,.6],atol=.003)
        self.assertLess(abs(theta[2]-3),.1)
        self.assertTrue(np.linalg.eigvalsh(cov).min()>0)

    def test_jacobian(self):
        p=self.problem();t=np.array([.2,-.3,2.]);eps=1e-5
        numerical=np.column_stack([(p.residual(t+eps*np.eye(3)[j])-p.residual(t-eps*np.eye(3)[j]))/(2*eps) for j in range(3)])
        np.testing.assert_allclose(p.jacobian(t),numerical,rtol=1e-7,atol=1e-7)

    def test_correlated_error_positive(self):
        t=np.arange("2019-09-01","2019-09-10",dtype="datetime64[D]")
        r=correlated_error(t,np.arange(9)*10,np.arange(9)%2==0)
        self.assertGreater(np.linalg.eigvalsh(r).min(),0)
        self.assertGreater(r[0,1],0)

    def test_rank_diagnostics_detect_shift(self):
        rng=np.random.default_rng(1);x=rng.normal(size=(4,2000,2))
        rh,ess=chain_diagnostics(x)
        self.assertTrue((rh<1.01).all());self.assertTrue((ess>3000).all())
        x[0,:,0]+=3
        self.assertGreater(chain_diagnostics(x)[0][0],1.1)

    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):
            InverseProblem(np.array([[np.nan]]),np.ones((1,1)),np.ones(1),np.eye(1),np.ones(2))

if __name__=="__main__":unittest.main()
