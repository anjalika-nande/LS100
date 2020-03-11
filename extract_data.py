import os
import pickle
import pylab as pl
import numpy as np

root_path = 'C:\LS100\LS100_free_swimming_4fish_data\phototaxis'
fish = '2020_03_09_fish038'

no_trials = 3
files = []

for i in range(no_trials):
    trial = i
    file= os.path.join(root_path, fish, "raw_data", "trial%03d.dat" % trial)
    files.append(file)

#pl.figure(1)
#pl.plot(data["raw_stimulus_000"]["fish_accumulated_orientation"])
#pl.plot(data["raw_stimulus_000"]["fish_orientation"])
#pl.show()


for i in range(no_trials):
    f = open(files[i], 'rb')
    data = pickle.load(f, encoding='latin1')
    f.close()
    pl.figure(2)
    pl.plot(data["raw_stimulus_000"]["fish_position_x"],
            data["raw_stimulus_000"]["fish_position_y"], alpha = 0.7)
    pl.plot(data["bouts_start_stimulus_000"]["fish_position_x"],
            data["bouts_start_stimulus_000"]["fish_position_y"], 'o', alpha = 0.7, label = 'Trial %i'%(i+1))
    pl.xlim(-1,1)
    pl.ylim(-1,1)
    pl.legend()
pl.show()


# print(data["bouts_start_stimulus_000"].keys())
#data["bouts_start_stimulus_000"][""]
# Histograms
for i in range(no_trials):
    f = open(files[i], 'rb')
    data = pickle.load(f, encoding='latin1')
    f.close()
    ibi = np.diff(data["bouts_start_stimulus_000"]["timestamp"])
    heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
    pl.figure(3)
    pl.hist(heading_angle_change, alpha = 0.7, label = 'Trial %i'%(i+1))
    pl.xlim(-180,180)
    pl.legend()
pl.show()






# heading_angle_change = data["bouts_end_stimulus_002"]["fish_accumulated_orientation"] - \
#                        data["bouts_start_stimulus_002"]["fish_accumulated_orientation"]
# pl.hist(heading_angle_change)
#
# pl.show()
#
# # print(data.keys())
# # pl.show()
# # print(data["raw_stimulus_000"].keys())
# # #print(data.keys())
