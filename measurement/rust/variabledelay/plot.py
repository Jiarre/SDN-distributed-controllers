import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np


m = ["1","10","100","1k","10k","100k","1M",'inf']
ticks = [1,10,100,1000,10000,100000,1000000,10000000]
frames1001 = []
frames10050 = []
frames100100 = []

for i in m:
    tmp = pd.read_csv(f'100peer1getter/{i}gets.csv').replace(0,np.nan)
    if i == 'inf':
        tmp['n'] = 10000000
    else:

        tmp['n'] = 1000000/tmp['micros']
    
    frames1001.append(tmp)
for i in m:
    tmp = pd.read_csv(f'100peer50getter/{i}gets.csv').replace(0,np.nan)
    if i == 'inf':
        tmp['n'] = 10000000
    else:

        tmp['n'] = 1000000/tmp['micros']
    
    frames10050.append(tmp)
for i in m:
    tmp = pd.read_csv(f'100peer100getter/{i}gets.csv').replace(0,np.nan)
    if i == 'inf':
        tmp['n'] = 10000000
    else:

        tmp['n'] = 1000000/tmp['micros']
    
    frames100100.append(tmp)


meanframes1001 = []
for df in frames1001:
    meanframes1001.append(df.groupby("n").median())
meanframes10050 = []
for df in frames10050:
    meanframes10050.append(df.groupby("n").median())
meanframes100100 = []
for df in frames100100:
    meanframes100100.append(df.groupby("n").median())


k1 = pd.concat(meanframes1001)
k1 = k1.loc[:, ~k1.columns.isin(['getter', 'peers','micros','payload'])]
k1 = k1.loc[~k1.index.duplicated(), :]
print(k1)
plt.plot(k1, label = "100 peers 1 getter")
    
k2 = pd.concat(meanframes10050)
k2 = k2.loc[:, ~k2.columns.isin(['getter', 'peers','micros','payload'])]
k2 = k2.loc[~k2.index.duplicated(), :]
print(k2)
plt.plot(k2, label = "100 peers 50 getters")
k3 = pd.concat(meanframes100100)
k3 = k3.loc[:, ~k3.columns.isin(['getter', 'peers','micros','payload'])]
k3 = k3.loc[~k3.index.duplicated(), :]
print(k3)
plt.plot(k3, label = "100 peers 100 getters")    
    

plt.legend()
plt.xscale("log")
plt.minorticks_off()
plt.xticks(ticks,m,rotation=45)
#plt.xscale("log")
plt.ylim(0,250)
plt.xlim(0,10000000)
plt.xlabel("Get per second (per getter)")
plt.ylabel("Delay (us)")
plt.grid(True,color="#D3D3D3")
plt.show()