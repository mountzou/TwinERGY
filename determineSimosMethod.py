import numpy as np
from collections import defaultdict


def determineWeights(preferences):

    res = defaultdict(list)
    for key, val in sorted(preferences.items()):
        res[val].append(key)

    sorted_res = sorted(res.items())

    importance_levels_exists = set()
    final_dict = [None] * 5

    for i, (key, val) in enumerate(sorted_res):
        importance_levels_exists.add(key)
        final_dict[key - 1] = val

    final_list = [final_dict[i - 1] if i in importance_levels_exists else ['w'] for i in range(1, 6)]

    subsets = final_list
    z = 6.5

    c = [len(subset) for subset in subsets if subset[0] != 'w']
    positions = len(c)
    no_cards = sum(c)

    U = round((z - 1) / positions, 6)
    e = np.ones(positions)

    e_index = 0
    for subset in subsets:
        if subset[0] == 'w':
            e[e_index - 1] += 1
        else:
            e_index += 1

    k = np.cumsum(np.concatenate(([1], U * e[:-1])))
    to_talk = np.dot(k, c)

    normalized_weights = (100 / to_talk) * k

    weight_array = {"Electric Vehicle": [], "Tumble Drier": [], "Washing Machine": [], "Dish Washer": [],
                    "Water Heater": []}

    appliance_mapping = {"Washing Machine": "Washing Machine", "Tumble Drier": "Tumble Drier",
                         "Electric Vehicle": "Electric Vehicle", "Dish Washer": "Dish Washer",
                         "Water Heater": "Water Heater"}

    normalized_weights_index = 0

    for i, subset in enumerate(subsets):
        if subset[0] != 'w':
            if normalized_weights_index < len(normalized_weights):
                weight = round(normalized_weights[normalized_weights_index], 2)
                for appliance in subset:
                    weight_array[appliance_mapping[appliance]].append(weight)
                normalized_weights_index += 1
            else:
                print(f"Missing weight for subset at index: {i}")
        else:
            print(f"Skipping 'w' at index: {i}")

    return weight_array
