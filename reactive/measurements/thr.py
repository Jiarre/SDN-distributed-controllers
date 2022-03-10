import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np


m = [1,2,3,4,10,20,30,40,100,200,300,400,1000,2000,3000]

frames = []

for i in m:
    tmp = pd.read_csv(f'{i}pkts.csv').replace(0,np.nan)
    tmp['n'] = i
    frames.append(tmp)


meanframes = []
for df in frames:
    df = df.drop(df[df.comm_type != 3].index)
    df['total_delay'] = df['Host_Delay'] + df['Border_Delay'] + df['SB_Delay'] + df['Controller_Delay']
    meanframes.append(df.groupby("n").median())



    
    
k = pd.concat(meanframes)
k = k.loc[:, ~k.columns.isin(['comm_type', 'SB_Delay',"total_delay"])]
k = k.loc[~k.index.duplicated(), :]
print(k)
#plt.plot(k['n'],k['total_delay'],color="red")
k.plot(kind="line",color=['cornflowerblue','navajowhite','lightsalmon'])
#sns.lineplot(x="n",err_style="band", ci='sd', estimator="median", data=k)
#k.plot(k['n'],k['Border_Delay'],color="navajowhite")
#k.plot(k['n'],k['Controller_Delay'],color="lightsalmon")
# loading dataset 


#sns.lineplot(x="comm_type", y="total_handling", data=data) 
#sns.histplot(data=data, x="controller",y="total_handling", multiple="stack") x="Communication Type",y="Time (ms)", 

# setting the title using Matplotlib
#plt.ylim(0,3)
plt.xlabel("Packets per second (pkt/s)")
plt.ylabel("Delay (ms)")

plt.show()