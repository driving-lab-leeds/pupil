import pickle
import os
import numpy as np

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

def closest_matches_monocular_surface(ref_pts, pupil_pts, surfaces, max_dispersion=1/15.):
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

    #surface timestamp
    surface_ts = np.array([s['timestamp'] for s in surfaces])

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

            #Do the same for surfaces
            closest_s_idx = find_nearest_idx(surface_ts, r['timestamp'])
            closest_s = surfaces[closest_s_idx]
            surf_dispersion = max(closest_s['timestamp'],r['timestamp']) - min(closest_s['timestamp'],r['timestamp'])

            if (dispersion < max_dispersion) and (surf_dispersion < max_dispersion):
                matched.append({'ref':r,'pupil':closest_p0, 'surface': closest_s})
            else:
                pass
    return matched

def get_marker_index(surf_ts, times):

    times = np.append(times, np.Inf)

    out = np.empty(surf_ts.size)
    out.fill(np.NaN)

    for i in range(times.size -1):

        marker_mask = np.logical_and(surf_ts < times[i + 1], surf_ts >= times[i])

        out[marker_mask] = i


    return out


os.chdir('pupil_src')

surface_list = pickle.load(open('surface_list.pkl', 'rb'))
test_markers = pickle.load(open('test_markers.pkl', 'rb'))

recent_input = pickle.load(open('recent_input.pkl', 'rb'))
recent_labels = pickle.load(open('recent_labels.pkl', 'rb'))

marker_times = np.array(pickle.load(open('marker_times.pkl', 'rb')))

#Make surface list one list
surface_list = [i for s in surface_list for i in s ]

#use recent input and recent_labels (ref pos)
matched = closest_matches_monocular(recent_input, recent_labels)#



#use recent input and recent_labels (ref pos)
matched_surf = closest_matches_monocular_surface(recent_input, recent_labels, surface_list)#

matched_surf_tf = np.array([s['ref']['timestamp'] for s in matched_surf])


marker_at_time = get_marker_index(matched_surf_tf, marker_times)


for i in range(len(test_markers)):
    m0 = np.array(matched_surf)[marker_at_time == i].tolist()

    norm_pos = [m['surface']['norm_pos'] for m in m0]

    error = (np.array(norm_pos) - test_markers[0])

    print(error.mean(0))

# [ 0.02223096 -0.09581757]
# [0.36504281 0.86058796]
# [ 0.525943   -0.04125193]
# [ 0.7160603  -0.04941413]
# [ 0.02084138 -0.32280151]
# [ 0.26827681 -0.32558271]
# [ 0.52576257 -0.3334589 ]
# [ 0.71733848 -0.33814626]
# [ 0.02499752 -0.62702349]
# [ 0.26846742 -0.64378789]
# [ 0.52300119 -0.62390594]
# [ 0.75235428 -0.59637357]

#TO DO:

# 1) Get the position they are looking at in normalised coordiantes corrolated with the recent inputs
# 2) Then figure out which marker they are looking at
# 3) Then perform accuracy test with whichever marker position they are looking at

