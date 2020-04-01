import os
import pickle
import pylab as pl
import matplotlib as mpl
import numpy as np
from matplotlib.lines import Line2D


WT_dark = [19, 21, 23, 29, 31]
WT_stimuli = [20, 22, 24, 30, 32]
MT_dark = [33, 37]
MT_stimuli = [34, 38]

all_fish = WT_dark + WT_stimuli + MT_dark + MT_stimuli
dates = ['2020_03_02_fish0', '2020_03_04_fish0','2020_03_06_fish0','2020_03_09_fish0']

# Creating a color map and defining legends
cmap = mpl.cm.hsv
colors = np.arange(0, len(all_fish)+1,1)*20

custom_WT_dark = [Line2D([0], [0], color=cmap(colors[0]), lw=4), Line2D([0], [0], color=cmap(colors[1]), lw=4),
             Line2D([0], [0], color=cmap(colors[2]), lw=4), Line2D([0], [0], color=cmap(colors[3]), lw=4),
             Line2D([0], [0], color=cmap(colors[4]), lw=4)]
custom_WT_stimuli = [Line2D([0], [0], color=cmap(colors[5]), lw=4),
             Line2D([0], [0], color=cmap(colors[6]), lw=4), Line2D([0], [0], color=cmap(colors[7]), lw=4),
             Line2D([0], [0], color=cmap(colors[8]), lw=4), Line2D([0], [0], color=cmap(colors[9]), lw=4)]

legend_WT_dark = ['Fish 19', 'Fish 21', 'Fish 23', 'Fish 29', 'Fish 31']
legend_WT_stimuli = ['Fish 20', 'Fish 22', 'Fish 24', 'Fish 30', 'Fish 32']

custom_mutant_dark = [Line2D([0], [0], color=cmap(colors[10]), lw=4), Line2D([0], [0], color=cmap(colors[11]), lw=4)]
custom_mutant_stimuli = [Line2D([0], [0], color=cmap(colors[12]), lw=4), Line2D([0], [0], color=cmap(colors[13]), lw=4)]

legend_mutant_dark = ['Fish 33', 'Fish 37']
legend_mutant_stimuli = ['Fish 34', 'Fish 38']
         
# Define file root path
root_path = '/Users/anjalikanande/rawdata'

# Generate plots
for indx, fish_no in enumerate(all_fish):
    
    if fish_no <= 24:
        fish = dates[0]+'%i'%fish_no
    elif 24 < fish_no <= 32:
        fish = dates[1]+'%i'%fish_no
    elif 32 < fish_no <= 34:
        fish = dates[2]+'%i'%fish_no
    else:
        fish = dates[3]+'%i'%fish_no
        
    no_trials = 3
    files = []

    for i in range(no_trials):
        trial = i
        file= os.path.join(root_path, fish, "raw_data", "trial%03d.dat" % trial)
        files.append(file)

    if indx <= 9:
        fish_type = 'Wild type'
    else: 
        fish_type = 'Mutant'
    # WT plots
    if fish_type == 'Wild type' and fish_no in WT_dark:
        
        for i in range(no_trials):
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            pl.figure(2, figsize = (8,6))
            pl.plot(data["raw_stimulus_000"]["fish_position_x"],
            data["raw_stimulus_000"]["fish_position_y"], alpha = 0.5, color = cmap(colors[indx]))
            pl.plot(data["bouts_start_stimulus_000"]["fish_position_x"],
            data["bouts_start_stimulus_000"]["fish_position_y"], 'o', alpha = 0.5, color = cmap(colors[indx]), label= 'Fish %i'%fish_no)
            pl.xlim(-1,1)
            pl.ylim(-1,1)
            pl.title(fish_type+' dark')
            pl.legend(custom_WT_dark,legend_WT_dark, bbox_to_anchor = (1.0,1.0))
            
            # Histogram
            ibi = np.diff(data["bouts_start_stimulus_000"]["timestamp"])
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            pl.figure(3, figsize = (8,6))
            pl.hist(heading_angle_change, alpha = 0.5, color = cmap(colors[indx]), label = 'Fish %i'%fish_no)
            pl.xlim(-180,180)
            pl.title(fish_type+' dark')
            
    elif fish_type == 'Wild type' and fish_no in WT_stimuli:
        
        for i in range(no_trials):
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            pl.figure(4, figsize = (8,6))
            pl.plot(data["raw_stimulus_000"]["fish_position_x"],
            data["raw_stimulus_000"]["fish_position_y"], alpha = 0.5, color = cmap(colors[indx]))
            pl.plot(data["bouts_start_stimulus_000"]["fish_position_x"],
            data["bouts_start_stimulus_000"]["fish_position_y"], 'o', alpha = 0.5, color = cmap(colors[indx]), label= 'Fish %i'%fish_no)
            pl.xlim(-1,1)
            pl.ylim(-1,1)
            pl.title(fish_type+' stimuli')
            pl.legend(custom_WT_stimuli,legend_WT_stimuli, bbox_to_anchor = (1.0,1.0))
            
            # Histogram
            ibi = np.diff(data["bouts_start_stimulus_000"]["timestamp"])
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            pl.figure(5, figsize = (8,6))
            pl.hist(heading_angle_change, alpha = 0.5, color = cmap(colors[indx]), label = 'Fish %i'%fish_no)
            pl.xlim(-180,180)
            pl.title(fish_type+' stimuli')
    else:
        # Mutant plots
        if fish_no in MT_dark:
            
            for i in range(no_trials):
                f = open(files[i], 'rb')
                data = pickle.load(f, encoding='latin1')
                f.close()
                pl.figure(6, figsize = (8,6))
                pl.plot(data["raw_stimulus_000"]["fish_position_x"],
                data["raw_stimulus_000"]["fish_position_y"], alpha = 0.5, color = cmap(colors[indx]))
                pl.plot(data["bouts_start_stimulus_000"]["fish_position_x"],
                data["bouts_start_stimulus_000"]["fish_position_y"], 'o', alpha = 0.5, color = cmap(colors[indx]))
                pl.xlim(-1,1)
                pl.ylim(-1,1)
                pl.title(fish_type+' dark')
                pl.legend(custom_mutant_dark,legend_mutant_dark)
                
            # Histogram
            ibi = np.diff(data["bouts_start_stimulus_000"]["timestamp"])
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            pl.figure(7, figsize = (8,6))
            pl.hist(heading_angle_change, alpha = 0.5, color = cmap(colors[indx]), label = 'Fish %i'%fish_no)
            pl.xlim(-180,180)
            pl.title(fish_type+' dark')
            
        elif fish_no in MT_stimuli:
            
            for i in range(no_trials):
                f = open(files[i], 'rb')
                data = pickle.load(f, encoding='latin1')
                f.close()
                pl.figure(8, figsize = (8,6))
                pl.plot(data["raw_stimulus_000"]["fish_position_x"],
                data["raw_stimulus_000"]["fish_position_y"], alpha = 0.5, color = cmap(colors[indx]))
                pl.plot(data["bouts_start_stimulus_000"]["fish_position_x"],
                data["bouts_start_stimulus_000"]["fish_position_y"], 'o', alpha = 0.5, color = cmap(colors[indx]))
                pl.xlim(-1,1)
                pl.ylim(-1,1)
                pl.title(fish_type+' stimuli')
                pl.legend(custom_mutant_stimuli,legend_mutant_stimuli)
                
            # Histogram
            ibi = np.diff(data["bouts_start_stimulus_000"]["timestamp"])
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            pl.figure(9, figsize = (8,6))
            pl.hist(heading_angle_change, alpha = 0.5, color = cmap(colors[indx]), label = 'Fish %i'%fish_no)
            pl.xlim(-180,180)
            pl.title(fish_type+' stimuli')
