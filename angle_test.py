import scipy.stats as stats
import numpy as np
from math import sqrt
from angle import angle_calculation
import seaborn as sn
import matplotlib.pyplot as plt
def angle_test(dist_a:float,dist_b:float,uwb_res:float)->tuple[float,float]:
    length = float(1.0)
    dist = float(3.536)
    real_val = np.arcsin((dist+length)/dist_b)-np.arcsin(dist/dist_a)
    residual = real_val-uwb_res
    return (np.rad2deg(real_val),np.rad2deg(residual)) 

if __name__ == "__main__":
    s_info=[[7.763 ,   8.232],[28.3,     28.420],[49.243  , 49.320]]
    for s in range(3):
        with open(f"s{s+1}","r") as f:
            file = f.readlines()
        data=[]
        for line in file:
            a = list(line.split(","))
            skip=False
            for i in range(len(a)):
                a[i]=float(a[i])
                if a[i]==0.0:
                    skip=True
            if not skip:
                data.append(a)
        #print(data)    
        residuals=[]
        values = [] 
        dist_a=s_info[s][0]
        dist_b = s_info[s][1] 
        length = float(1.0)
        dist = float(3.536)
        real = np.rad2deg(np.arcsin((dist+length)/dist_b)-np.arcsin(dist/dist_a))
        for record in data:
            deg = angle_calculation(record[0],record[2],1.0)[1]
            residuals.append(real - deg)
            values.append(deg)
        mbe = np.mean(residuals)
        mse = np.mean([pow(x,2) for x in residuals])
        stat, p = stats.ttest_1samp(values,real)
        interval = stats.t.interval(confidence=0.90, df=len(values)-1,
              loc=np.mean(values),
              scale=stats.sem(values))
        print(f'For {s+1} angle calculation:')
        print(f'\tReference values were: {s_info[s],3}, angle value: {round(real,3)}, number of measurement: {len(values)}')
        print(f'\tNull hyphothesis, mean result from angle stimation is equal to real angle value, results: t statistic value: {round(stat,3)}, p_value: {round(p,3)}. Null hypothesis is rejected: {p<0.05}')
        print(f'\tMSE is equal to {round(mse,3)} degrees\n\tRMSE is equal to {round(sqrt(mse),3)} degrees, \n\tMBE is equal to {round(mbe,3)} degrees.\n\tMbe is {round(mbe/real*100,3)}% of real value')
        print(f"\tConfidence interval is equal to {interval} in degrees")
