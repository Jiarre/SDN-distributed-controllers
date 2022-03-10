import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

data = pd.read_csv('dataset_final.csv')  
# loading dataset 
 
tmp = data.replace(0,np.nan).groupby('comm_type').mean()
maximum = data.replace(0,np.nan).groupby('comm_type').max()
mean = data.replace(0,np.nan).groupby('comm_type').mean()

print(maximum)
print(mean)
print(tmp)
#sns.lineplot(x="comm_type", y="total_handling", data=data) 
#sns.histplot(data=data, x="controller",y="total_handling", multiple="stack") x="Communication Type",y="Time (ms)", 
tmp.plot(kind='bar', stacked=True, color=['steelblue','cornflowerblue','navajowhite','lightsalmon'])
plt.xticks(rotation=45)
# setting the title using Matplotlib
plt.ylim(0,15)
plt.xlabel('Communication Type')
plt.ylabel('Time(ms)')
plt.show()