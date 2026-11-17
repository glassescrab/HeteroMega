import numpy as np, glob, os, statistics, sys
def lsm(x): x=x.astype(np.float64); m=x.max(); return x-m-np.log(np.exp(x-m).sum())
for qd,L in (("quality-v4",1024),("quality-v4-4096",4096)):
    seeds=sorted(glob.glob(f"{qd}/seed*"))
    cells=["gpu_original-%d-r0"%L,"gpu_original-%d-r1"%L,"G1-%d-r0"%L,"O1-%d-r0"%L,"H1-%d-r0"%L,"HT1-%d-r0"%L]
    for ref in ("gpu_original-%d-r0"%L,"G1-%d-r0"%L):
        print(f"== {qd} ref={ref} seeds={len(seeds)}")
        for c in cells:
            if c==ref: continue
            kl=[];top=[]
            for sd in seeds:
                a=f"{sd}/{ref}.npz"; b=f"{sd}/{c}.npz"
                if not (os.path.exists(a) and os.path.exists(b)): continue
                p=lsm(np.load(a)["logits"]); q=lsm(np.load(b)["logits"])
                kl.append(float((np.exp(p)*(p-q)).sum())); top.append(int(p.argmax()==q.argmax()))
            if kl: print(f"  {c:24s} n={len(kl)} median KL={statistics.median(kl):.2e} top1={sum(top)}/{len(top)}")
