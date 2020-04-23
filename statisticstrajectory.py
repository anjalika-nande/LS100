import os
import pickle
import numpy as np



WT_dark = [19, 21, 23, 29, 31]
WT_stimuli = [20, 22, 24, 30, 32]
MT_dark = [33, 37]
MT_stimuli = [34, 38]

all_fish = WT_dark + WT_stimuli + MT_dark + MT_stimuli
dates = ['2020_03_02_fish0', '2020_03_04_fish0','2020_03_06_fish0','2020_03_09_fish0']
         
# Define file root path
root_path = '/Users/anjalikanande/rawdata'

# Insert statistics
WT_dark_right = []
WT_stimulus_right = []
MT_dark_right = []
MT_stimulus_right = []

WT_dark_x = []
WT_dark_y = []
WT_stimulus_x = []
WT_stimulus_y = []
MT_dark_x = []
MT_dark_y = []
MT_stimulus_x = []
MT_stimulus_y = []


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
        frac_right_dish = 0
        x_dist = 0
        y_dist = 0
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            x_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_x"] if str(i) != 'nan']
            y_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_y"] if str(i) != 'nan']
            x_dist += sum([np.abs(x_position[i+1] - x_position[i]) for i in range(len(x_position)-1)])
            y_dist += sum([np.abs(y_position[i+1] - y_position[i]) for i in range(len(y_position)-1)])
            frac_right_dish += sum([i for i in np.sign(x_position) if i > 0])/len(x_position)
        avg_position_right_dish = frac_right_dish/no_trials
        WT_dark_right.append(avg_position_right_dish)
        WT_dark_x.append(x_dist)
        WT_dark_y.append(y_dist)
    
    elif fish_type == 'Wild type' and fish_no in WT_stimuli:
        frac_right_dish = 0
        x_dist = 0
        y_dist = 0
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            x_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_x"] if str(i) != 'nan']
            y_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_y"] if str(i) != 'nan']
            x_dist += sum([np.abs(x_position[i+1] - x_position[i]) for i in range(len(x_position)-1)])
            y_dist += sum([np.abs(y_position[i+1] - y_position[i]) for i in range(len(y_position)-1)])
            frac_right_dish += sum([i for i in np.sign(x_position) if i > 0])/len(x_position)
        avg_position_right_dish = frac_right_dish/no_trials
        WT_stimulus_right.append(avg_position_right_dish)
        WT_stimulus_x.append(x_dist)
        WT_stimulus_y.append(y_dist)
        
    elif fish_type == 'Mutant' and fish_no in MT_dark:
        frac_right_dish = 0
        x_dist = 0
        y_dist = 0
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            x_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_x"] if str(i) != 'nan']
            y_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_y"] if str(i) != 'nan']
            x_dist += sum([np.abs(x_position[i+1] - x_position[i]) for i in range(len(x_position)-1)])
            y_dist += sum([np.abs(y_position[i+1] - y_position[i]) for i in range(len(y_position)-1)])
            frac_right_dish += sum([i for i in np.sign(x_position) if i > 0])/len(x_position)
        avg_position_right_dish = frac_right_dish/no_trials
        MT_dark_right.append(avg_position_right_dish)
        MT_dark_x.append(x_dist)
        MT_dark_y.append(y_dist)
        
    elif fish_type == 'Mutant' and fish_no in MT_stimuli:
        frac_right_dish = 0
        x_dist = 0
        y_dist = 0
        for i in range(no_trials):
            
            f = open(files[i], 'rb')
            data = pickle.load(f, encoding='latin1')
            f.close()
            x_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_x"] if str(i) != 'nan']
            y_position = [i for i in data["bouts_start_stimulus_000"]["fish_position_y"] if str(i) != 'nan']
            x_dist += sum([np.abs(x_position[i+1] - x_position[i]) for i in range(len(x_position)-1)])
            y_dist += sum([np.abs(y_position[i+1] - y_position[i]) for i in range(len(y_position)-1)])
            frac_right_dish += sum([i for i in np.sign(x_position) if i > 0])/len(x_position)
        avg_position_right_dish = frac_right_dish/no_trials
        MT_stimulus_right.append(avg_position_right_dish)
        MT_stimulus_x.append(x_dist)
        MT_stimulus_y.append(y_dist)

# Could also compute the variance      
avg_WT_dark_right = np.average(WT_dark_right)
avg_WT_stimulus_right = np.average(WT_stimulus_right)
avg_MT_dark_right = np.average(MT_dark_right)
avg_MT_stimulus_right = np.average(MT_stimulus_right)

print('WT in darkness on average spend %.2f fraction of the time on the right side of the dish'%avg_WT_dark_right)
print('WT exposed to stimulus on average spend %.2f fraction of the time on the right side of the dish'%avg_WT_stimulus_right)

print('MT in darkness on average spend %.2f fraction of the time on the right side of the dish'%avg_MT_dark_right)
print('MT exposed to stimulus on average spend %.2f fraction of the time on the right side of the dish'%avg_MT_stimulus_right)
            
# Average dist covered by WT and MT. Figure out the units!!!!
avg_WT_dark_dist = np.sqrt(np.average(WT_dark_x)**2 + np.average(WT_dark_y)**2)
avg_WT_stimulus_dist = np.sqrt(np.average(WT_stimulus_x)**2 + np.average(WT_stimulus_y)**2)
avg_MT_dark_dist = np.sqrt(np.average(MT_dark_x)**2 + np.average(MT_dark_y)**2)
avg_MT_stimulus_dist = np.sqrt(np.average(MT_stimulus_x)**2 + np.average(MT_stimulus_y)**2)

print('')
print('WT in darkness on average cover a distance of %.2f'%avg_WT_dark_dist)
print('WT under stimulus on average cover a distance of %.2f'%avg_WT_stimulus_dist)
print('MT in darkness on average cover a distance of %.2f'%avg_MT_dark_dist)
print('MT under stimulus on average cover a distance of %.2f'%avg_MT_stimulus_dist)
            
            
            
            
            
            
            
            