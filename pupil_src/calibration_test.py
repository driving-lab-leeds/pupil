import pickle
import os

os.chdir('pupil_src')
pupil_list = pickle.load(open('pupil_list.pkl', 'rb'))
ref_list = pickle.load(open('pupil_list.pkl', 'rb'))
surface_list = pickle.load(open('pupil_list.pkl', 'rb'))

print(pupil_list)