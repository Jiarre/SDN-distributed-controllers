import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

folders = ["1peer","2peer","4peer","8peer","16peer","32peer","64peer","128peer","256peer","512peer","1024peer"]
#folders = ["64byte","128byte","256byte","512byte","1Kbyte","2Kbyte","4Kbyte","8Kbyte","16Kbyte","32Kbyte","64Kbyte","128Kbyte","256Kbyte","512Kbyte","1Mbyte","2Mbyte","4Mbyte","8Mbyte","16Mbyte","32Mbyte","64Mbyte","128Mbyte","256Mbyte","512Mbyte"]
folders.reverse()   
m = ["1","10","100","1k","10k","100k","1M",'inf']
ticks = [1,10,100,1000,10000,100000,1000000,10000000]


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
    plt.plot(k1, label = f"{f}")



    


plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.xscale("log")
plt.yscale("log")
plt.minorticks_off()
plt.xticks(ticks,m,rotation=45)
plt.yticks(ticks,rotation=45)
plt.minorticks_off()
plt.xlabel("Get per second (per getter)")
plt.ylabel("Delay (us)")
plt.grid(True,color="#D3D3D3")
plt.show()