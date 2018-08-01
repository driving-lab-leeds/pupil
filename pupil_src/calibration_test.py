import pickle
import os

def closest_matches_monocular(ref_pts, pupil_pts, max_dispersion=1/15.):
    '''
    get pupil positions closest in time to ref points.
    return list of dict with matching ref and pupil datum.

    if your data is binocular use:
    pupil0 = [p for p in pupil_pts if p['id']==0]
    pupil1 = [p for p in pupil_pts if p['id']==1]
    to get the desired eye and pass it as pupil_pts
    '''

    ref = ref_pts
    pupil0 = pupil_pts
    pupil0_ts = np.array([p['timestamp'] for p in pupil0])

    def find_nearest_idx(array,value):
        idx = np.searchsorted(array, value, side="left")
        try:
            if abs(value - array[idx-1]) < abs(value - array[idx]):
                return idx-1
            else:
                return idx
        except IndexError:
            return idx-1

    matched = []
    if pupil0:
        for r in ref_pts:
            closest_p0_idx = find_nearest_idx(pupil0_ts,r['timestamp'])
            closest_p0 = pupil0[closest_p0_idx]
            dispersion = max(closest_p0['timestamp'],r['timestamp']) - min(closest_p0['timestamp'],r['timestamp'])
            if dispersion < max_dispersion:
                matched.append({'ref':r,'pupil':closest_p0})
            else:
                pass
    return matched


os.chdir('pupil_src')

surface_list = pickle.load(open('surface_list.pkl', 'rb'))
test_markers = pickle.load(open('test_markers.pkl', 'rb'))

recent_input = pickle.load(open('recent_input.pkl', 'rb'))
recent_labels = pickle.load(open('recent_labels.pkl', 'rb'))


#use recent input and recent_labels (ref pos)
matched = closest_matches_monocular(recent_input, recent_labels)#



#TO DO:

# 1) Get the position they are looking at in normalised coordiantes corrolated with the recent inputs
# 2) Then figure out which marker they are looking at
# 3) Then perform accuracy test with whichever marker position they are looking at