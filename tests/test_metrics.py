import numpy as np
from src.pipeline import group_age,normalize_name

def test_age_bins():
 assert list(group_age([18,24,25,34,35,44,45,59,60,99]).astype(str)) == ['18-24','18-24','25-34','25-34','35-44','35-44','45-59','45-59','60+','60+']
def test_municipal_normalization():
 assert normalize_name('San José (Del Valle)')=='SANJOSEDELVALLE'
def test_denominator():
 sv,nv,ns=60,40,20
 assert sv/(sv+nv)==.6
 assert sv/(sv+nv+ns)!=.6
