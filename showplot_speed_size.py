import seaborn as sns; sns.set()
import matplotlib.pyplot as plt
import numpy as np

#CF, 
y = np.array([50.8, 50.2, 49.7, 49.1, 48.5, 48.3, 48.2, 48.1, 48.1])
x = np.array([444, 310, 295, 285, 254, 233, 214, 152, 125])
ax = sns.lineplot(x, y)
#NG
y = np.array([50.7, 50.7, 49.6, 48.7, 48.4, 48.2, 48, 48, 47.9])
x = np.array([295, 295, 275, 243, 218, 193, 143, 111, 93])
ax = sns.lineplot(x, y)
#Sys
y = np.array([51.4, 50.5, 49.8, 49.1, 48.5, 48.1, 48, 48, 47.9])
x = np.array([266, 256, 228, 222, 191, 159, 129, 106, 86])
ax = sns.lineplot(x, y)
#gzip
y = np.array([51.4, 50.6, 49.9, 49.2, 48.5, 48.1, 48, 47.9, 47.9])
x = np.array([70, 68, 59, 56, 47, 35, 30, 21, 17])
ax = sns.lineplot(x, y)
#pbzip2, 
y = np.array([45.6, 44.7, 44.2, 44.1, 43.9, 43.8, 43.8, 43.6, 43.4])
x = np.array([68, 67, 65, 61, 59, 56, 54, 51, 47])
ax = sns.lineplot(x, y)
#zstd
y = np.array([50.1, 48.7, 47.6, 47.2, 46.6, 46.3, 45.7, 45.5, 45.3, 45, 44.9, 44.8, 44.5, 44.3, 44.2, 43.6, 43.2, 42.9, 42.7])
x = np.array([950, 779, 512, 350, 181, 138, 117, 97, 77, 57, 47, 33, 31, 25, 20, 16, 12, 10, 8])
ax = sns.lineplot(x, y)

labels  = ['pigzCF','pigzNG','pigzSys','gzip','pbzip2','zstd']
plt.legend(labels) 
plt.title('Compression Speed vs Size')
plt.xlabel('Speed (mb/s, more=faster)')
plt.ylabel('Compression % (less=smaller)') 

plt.show()