import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
sns.set()

x = np.array([1, 2, 4, 8, 16, 24, 32, 48])

colors  = ['r','b','g']
plt.title('Compression Speed (3=dotted, 6=solid, 9=dashed)')
plt.xlabel('Cores')
plt.ylabel('Acceleration (vs 1 core with System zlib)')
labels  = ['System','ng','CloudFlare']

#Level 6 = default
#time in milliseconds as a function of number of cores
cf = np.array([33241,17116,8994,4844,2690,2208,2058,2249])
ng = np.array([49822,25610,13409,7137,3868,2896,2556,2695])
sys = np.array([66507,33813,17572,9374,5067,3703,3214,3176])
#acceleration relative to pigz (system zlib) using single core
cf = sys[0]/cf
ng = sys[0]/ng
sys = sys[0]/sys
lines = [sys,ng,cf]
for i,c,l in zip(lines,colors,labels):  
    plt.plot(x,i,c,label='l')
    plt.legend(labels)    

#Level 9 = slowest
#time in milliseconds as a function of number of cores
cf = np.array([57532,29475,15391,8160,4425,3276,2917,2970])
ng = np.array([198453,99975,51397,27177,14382,10195,8542,7146])
sys = np.array([183077,91591,47132,24887,13215,9393,7857,6675])
#acceleration relative to pigz (system zlib) using single core
cf = sys[0]/cf
ng = sys[0]/ng
sys = sys[0]/sys
lines = [sys,ng,cf]
for i,c,l in zip(lines,colors,labels):  
    plt.plot(x,i,c,label='l',linestyle="--")

#Level 3 = fast
#time in milliseconds as a function of number of cores
cf = np.array([20958,11034,5867,3183,1833,1675,1705,1888])
ng = np.array([29556,15388,8097,4377,2450,1930,1834,2021])
sys = np.array([34667,17947,9423,5060,2817,2194,1991,2261])
#acceleration relative to pigz (system zlib) using single core
cf = sys[0]/cf
ng = sys[0]/ng
sys = sys[0]/sys
lines = [sys,ng,cf]
for i,c,l in zip(lines,colors,labels):  
    plt.plot(x,i,c,label='l',linestyle=":")

plt.show()

