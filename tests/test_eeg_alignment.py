import pandas as pd
from pcs_toolbox.zuco import _aggregate_eeg

def test_aggregate_eeg_mean():
    df = pd.DataFrame({
        "Dataset":["v1","v1"],"Task":["NR","NR"],"Subject":["S1","S1"],
        "SentenceID":[1,1],"w_pos":[3,3],"token_norm":["the","the"],
        "theta1":[0.2,0.4],"alpha1":[0.1,0.3],"beta1":[0.05,0.07],"gamma1":[0.01,0.02]
    })
    out = _aggregate_eeg(df)
    row = out.iloc[0]
    assert abs(row.theta1 - 0.3) < 1e-9
    assert abs(row.alpha1 - 0.2) < 1e-9
