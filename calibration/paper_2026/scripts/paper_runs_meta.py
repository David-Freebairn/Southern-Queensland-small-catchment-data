W = '/home/claude/Watbal2026/'
D = '/home/claude/southern-queensland-small-catchment-data/'
CLIM = {'Greenmount': 'Greenmount catchment.P51', 'Greenwood': 'Greenwood catchmenr.p51', 'Wallumbilla': 'Wallumbilla catchment.p51'}
OLD_SOIL = {'Greenmount': D + 'greenmount/model_files/Black_earth.soil', 'Greenwood': D + 'greenwood/model_files/Greenwood_Grey_clay.soil',
            'Wallumbilla': D + 'wallumbilla/model_files/Brown_sodosol.soil'}
NEW_SOIL = {('Greenmount', False): 'Greenmount_Black_earth_2026.soil', ('Greenmount', True): 'Greenmount_Black_earth_2026_zero_till.soil',
            ('Greenwood', False): 'Greenwood_Grey_clay_2026.soil', ('Greenwood', True): 'Greenwood_Grey_clay_2026_zero_till.soil',
            ('Wallumbilla', False): 'Wallumbilla_Brown_sodosol_2026.soil'}
VEGE = {('Greenmount', 'Burnt'): 'Greenmount_wheat_stubble_burnt', ('Greenmount', 'Incorporated'): 'Greenmount_wheat_stubble_incorporated',
        ('Greenmount', 'Mulch'): 'Greenmount_wheat_stubble_mulch', ('Greenmount', 'Zero till'): 'Greenmount_Wheat_zero_till',
        ('Greenwood', 'Burnt'): 'Greenwood_wheat_stubble_burnt', ('Greenwood', 'Incorporated'): 'Greenwood_wheat_stubble_incorporated',
        ('Greenwood', 'Mulch'): 'Greenwood_wheat_stubble_mulch', ('Greenwood', 'Zero till'): 'Greenwood_Wheat_zero_till',
        ('Wallumbilla', 'Tilled'): 'Wallumbilla_chisel', ('Wallumbilla', 'Min till'): 'Wallumbilla_Minimum_tillage'}
B_SS = 0.0388
