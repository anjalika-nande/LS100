import os
import pickle
import numpy as np
import matplotlib as mpl
import scipy.stats as ss
import scipy.optimize as so
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def likelihood_norm(para,x,neg=-1):
    L=(-len(x)*np.log(2*np.pi)/2)-(len(x)*np.log(para[1]**2)/2)-1/2*(sum((x-para[0])**2/para[1]**2))
    return neg*L


WT_dark = [19, 21, 23, 29, 31]
WT_stimuli = [20, 22, 24, 30, 32]
MT_dark = [33, 37]
MT_stimuli = [34, 38]
all_fish = WT_dark + WT_stimuli + MT_dark + MT_stimuli
# Creating a color map and defining legends
cmap = mpl.cm.hsv
colors = np.arange(0, len(all_fish)+1,1)*20

custom_WT_dark = [Line2D([0], [0], color=cmap(colors[0]), lw=4), Line2D([0], [0], color=cmap(colors[1]), lw=4),
             Line2D([0], [0], color=cmap(colors[2]), lw=4), Line2D([0], [0], color=cmap(colors[3]), lw=4),
             Line2D([0], [0], color=cmap(colors[4]), lw=4)]
custom_WT_stimuli = [Line2D([0], [0], color=cmap(colors[5]), lw=4),
             Line2D([0], [0], color=cmap(colors[6]), lw=4), Line2D([0], [0], color=cmap(colors[7]), lw=4),
             Line2D([0], [0], color=cmap(colors[8]), lw=4), Line2D([0], [0], color=cmap(colors[9]), lw=4)]

custom_mutant_dark = [Line2D([0], [0], color=cmap(colors[10]), lw=4), Line2D([0], [0], color=cmap(colors[11]), lw=4)]
custom_mutant_stimuli = [Line2D([0], [0], color=cmap(colors[12]), lw=4), Line2D([0], [0], color=cmap(colors[13]), lw=4)]

dates = ['2020_03_02_fish0', '2020_03_04_fish0','2020_03_06_fish0','2020_03_09_fish0']
         
# Define file root path
root_path = '/Users/anjalikanande/rawdata'

# Insert statistics
WT_dark_angle = []
WT_stimulus_angle = []
MT_dark_angle = []
MT_stimulus_angle = []

value_norm_WT_dark = []
value_norm_WT_stimulus = []
value_norm_MT_dark = []
value_norm_MT_stimulus = []

total_heading_WT_dark = []
total_heading_WT_stimulus = []
total_heading_MT_dark = []
total_heading_MT_stimulus = []
# Generate statistics about the fish trajectories
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
        heading_angle_all_trials = []
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            heading_angle_all_trials.extend(heading_angle_change)
        heading_angle_all_trials = [i for i in heading_angle_all_trials if str(i) != 'nan']
        total_heading_WT_dark.extend(heading_angle_all_trials)
        result_norm=so.fmin(likelihood_norm,[1,1],args=(heading_angle_all_trials,-1), full_output=True, disp=False)  
        value_norm_WT_dark.append(result_norm[0])
        plt.figure(1, figsize=(8,6))
        plt.plot(np.arange(-150,151,1),ss.norm.pdf(np.arange(-150,151,1),loc=result_norm[0][0],scale=result_norm[0][1]),color = cmap(colors[indx]))
        plt.title('MLE results for WT fish in the dark')
        #plt.savefig('WTdarkMLE.png',bbox_inches='tight')
        plt.figure(5,figsize=(8,6))
        plt.hist(np.abs(heading_angle_all_trials), density='True',color = cmap(colors[indx]), alpha = 0.5)
        WT_dark_angle.append([np.average(heading_angle_all_trials), np.var(heading_angle_all_trials)])
        
    
    elif fish_type == 'Wild type' and fish_no in WT_stimuli:
        heading_angle_all_trials = []
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            heading_angle_all_trials.extend(heading_angle_change)
        heading_angle_all_trials = [i for i in heading_angle_all_trials if str(i) != 'nan'] 
        total_heading_WT_stimulus.extend(heading_angle_all_trials)
        result_norm=so.fmin(likelihood_norm,[1,1],args=(heading_angle_all_trials,-1), full_output=True, disp=False)  
        value_norm_WT_stimulus.append(result_norm[0])
        
        plt.figure(2,figsize=(8,6))
        plt.plot(np.arange(-150,151,1),ss.norm.pdf(np.arange(-150,151,1),loc=result_norm[0][0],scale=result_norm[0][1]),color = cmap(colors[indx]))
        plt.title('MLE results for WT fish exposed to stimulus')
        #plt.savefig('WTstimulusMLE.png',bbox_inches='tight')
        plt.figure(6,figsize=(8,6))
        plt.hist(np.abs(heading_angle_all_trials), density='True',color = cmap(colors[indx]), alpha = 0.5)
        WT_stimulus_angle.append([np.average(heading_angle_all_trials), np.var(heading_angle_all_trials)])
        
    elif fish_type == 'Mutant' and fish_no in MT_dark:
        heading_angle_all_trials = []
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            heading_angle_all_trials.extend(heading_angle_change)
        heading_angle_all_trials = [i for i in heading_angle_all_trials if str(i) != 'nan']  
        total_heading_MT_dark.extend(heading_angle_all_trials)
        result_norm=so.fmin(likelihood_norm,[1,1],args=(heading_angle_all_trials,-1), full_output=True, disp=False)  
        value_norm_MT_dark.append(result_norm[0])
        plt.figure(3,figsize=(8,6))
        plt.plot(np.arange(-150,151,1),ss.norm.pdf(np.arange(-150,151,1),loc=result_norm[0][0],scale=result_norm[0][1]),color = cmap(colors[indx]))
        plt.title('MLE results for MT fish in darkness')
        #plt.savefig('MTdarkMLE.png',bbox_inches='tight')
        plt.figure(7,figsize=(8,6))
        plt.hist(np.abs(heading_angle_all_trials), density='True',color = cmap(colors[indx]), alpha = 0.5)
        MT_dark_angle.append([np.average(heading_angle_all_trials), np.var(heading_angle_all_trials)])
        
    elif fish_type == 'Mutant' and fish_no in MT_stimuli:
        heading_angle_all_trials = []
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            heading_angle_change = data["bouts_end_stimulus_000"]["fish_accumulated_orientation"] - \
                       data["bouts_start_stimulus_000"]["fish_accumulated_orientation"]
            heading_angle_all_trials.extend(heading_angle_change)
        heading_angle_all_trials = [i for i in heading_angle_all_trials if str(i) != 'nan']   
        total_heading_MT_stimulus.extend(heading_angle_all_trials)
        result_norm=so.fmin(likelihood_norm,[1,1],args=(heading_angle_all_trials,-1), full_output=True, disp=False)  
        value_norm_MT_stimulus.append(result_norm[0])
        plt.figure(4,figsize=(8,6))
        plt.plot(np.arange(-150,151,1),ss.norm.pdf(np.arange(-150,151,1),loc=result_norm[0][0],scale=result_norm[0][1]),color = cmap(colors[indx]))
        plt.title('MLE results for MT fish exposed to stimulus')
        #plt.savefig('MTstimulusMLE.png',bbox_inches='tight')
        plt.figure(8,figsize=(8,6))
        plt.hist(np.abs(heading_angle_all_trials), density='True',color = cmap(colors[indx]), alpha = 0.5)
        MT_stimulus_angle.append([np.average(heading_angle_all_trials), np.var(heading_angle_all_trials)])

# Average mean and variance
WT_dark_avg = np.sum(WT_dark_angle, axis = 0)/len(WT_dark_angle)
WT_stimulus_avg = np.sum(WT_stimulus_angle, axis = 0)/len(WT_stimulus_angle)
MT_dark_avg = np.sum(MT_dark_angle, axis = 0)/len(MT_dark_angle)
MT_stimulus_avg = np.sum(WT_stimulus_angle, axis = 0)/len(MT_stimulus_angle)
            
print('Mean angle of turns for the WT in the dark is %.2f with standard deviation %.2f'%(WT_dark_avg[0],np.sqrt(WT_dark_avg[1])))
print('Mean angle of turns for the WT under stimulus is %.2f with standard deviation %.2f'%(WT_stimulus_avg[0],np.sqrt(WT_stimulus_avg[1])))
print('Mean angle of turns for the MT in the dark is %.2f with standard deviation %.2f'%(MT_dark_avg[0],np.sqrt(MT_dark_avg[1])))
print('Mean angle of turns for the MT under stimulus is %.2f with standard deviation %.2f'%(MT_stimulus_avg[0],np.sqrt(MT_stimulus_avg[1])))            
plt.figure(9, figsize=(8,6))
plt.hist(np.abs(total_heading_WT_stimulus), density = 'True')
plt.title('Aggregated absolute value of angle of turns for WT exposed to stimulus')

plt.figure(10, figsize=(8,6))
plt.hist(np.abs(total_heading_WT_dark), density = 'True')
plt.title('Aggregated absolute value of angle of turns for WT control')

plt.figure(11, figsize=(8,6))
plt.hist(np.abs(total_heading_MT_stimulus), density = 'True')
plt.title('Aggregated absolute value of angle of turns for MT exposed to stimulus')

plt.figure(12, figsize=(8,6))
plt.hist(np.abs(total_heading_MT_dark), density = 'True')
plt.title('Aggregated absolute value of angle of turns for MT control')
            

