import seaborn as sns 
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np

data = pd.read_csv('data.csv')  
# loading dataset 
 

#sns.lineplot(x="comm_type", y="total_handling", data=data) 
#sns.histplot(data=data, x="controller",y="total_handling", multiple="stack") x="Communication Type",y="Time (ms)", 
data.replace(0,np.nan).groupby('comm_type').mean().plot(kind='bar', stacked=True, color=['steelblue','cornflowerblue','navajowhite','lightsalmon'])
plt.xticks(rotation=45)
# setting the title using Matplotlib
plt.title('Average Delays')
plt.ylim(0,14)
plt.xlabel('Communication Type')
plt.ylabel('Time(ms)')
plt.show()