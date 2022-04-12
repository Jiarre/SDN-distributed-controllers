import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

folders = ["32byte","128Kbyte","256Kbyte","512Kbyte","1Mbyte","2Mbyte","4Mbyte","8Mbyte","16Mbyte","32Mbyte","64Mbyte","128Mbyte"]
m = ["1","10","100","1k","10k","100k","1M",'inf']
ticks = [1,10,100,1000,10000,100000,1000000,10000000]
folders.reverse()   

frames32= []
frames64= []

for f in folders:
    frames = []
    for i in m:
        tmp = pd.read_csv(f'{f}/{i}gets.csv').replace(0,np.nan)
        if i == 'inf':
            tmp['n'] = 10000000
        else:

            tmp['n'] = 1000000/tmp['micros']
        
        frames.append(tmp)
    meanframes = []
    for df in frames:
        meanframes.append(df.groupby("n").median())
    k1 = pd.concat(meanframes)
    k1 = k1.loc[:, ~k1.columns.isin(['getter', 'peers','micros','payload','rcv_flag'])]
    k1 = k1.loc[~k1.index.duplicated(), :]
    print(f"Printing {f}")
    print(k1)
    plt.plot(k1, label = f"{f} payload")
"""for i in m:
    tmp = pd.read_csv(f'32byte/{i}gets.csv').replace(0,np.nan)
    if i == 'inf':
        tmp['n'] = 10000000
    else:

        tmp['n'] = 1000000/tmp['micros']
    
    frames32.append(tmp)

for i in m:
    tmp = pd.read_csv(f'64byte/{i}gets.csv').replace(0,np.nan)
    if i == 'inf':
        tmp['n'] = 10000000
    else:

        tmp['n'] = 1000000/tmp['micros']
    
    frames64.append(tmp)

meanframes32 = []
for df in frames32:
    meanframes32.append(df.groupby("n").median())

meanframes64 = []
for df in frames64:
    meanframes64.append(df.groupby("n").median())



k1 = pd.concat(meanframes32)
k1 = k1.loc[:, ~k1.columns.isin(['getter', 'peers','micros','payload'])]
k1 = k1.loc[~k1.index.duplicated(), :]
print(k1)
plt.plot(k1, label = "32 bytes payload")

k2 = pd.concat(meanframes64)
k2 = k2.loc[:, ~k2.columns.isin(['getter', 'peers','micros','payload'])]
k2 = k2.loc[~k1.index.duplicated(), :]
print(k2)
plt.plot(k2, label = "64 bytes payload")"""


    


plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.xscale("log")
plt.minorticks_off()
plt.yscale("log")
plt.xticks(ticks,m,rotation=45)
plt.yticks(ticks)
#plt.xscale("log")

plt.xlim(0,10000000)
plt.xlabel("Get per second (per getter)")
plt.ylabel("Delay (us)")
plt.grid(True,color="#D3D3D3")
plt.show()