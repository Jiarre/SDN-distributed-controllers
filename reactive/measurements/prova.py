import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

data = pd.read_csv('data.csv')  
# loading dataset 
 
tmp = data.replace(0,np.nan).groupby('comm_type').median()
maximum = data.replace(0,np.nan).groupby('comm_type').max()
mean = data.replace(0,np.nan).groupby('comm_type').mean()

print(maximum)
print(mean)
print(tmp)
#sns.lineplot(x="comm_type", y="total_handling", data=data) 
#sns.histplot(data=data, x="controller",y="total_handling", multiple="stack") x="Communication Type",y="Time (ms)", 
tmp = tmp.loc[:, ~tmp.columns.isin([ 'SB_Delay'])]

tmp.plot(kind='bar', stacked=True, color=['cornflowerblue','navajowhite','lightsalmon'])
plt.xticks(rotation=45)
# setting the title using Matplotlib
plt.xlabel('Communication Type')
plt.ylabel('Time(us)')
plt.show()