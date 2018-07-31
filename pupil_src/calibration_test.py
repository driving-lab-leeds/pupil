import pickle
import os

os.chdir('pupil_src')

surface_list = pickle.load(open('surface_list.pkl', 'rb'))

print(surface_list)