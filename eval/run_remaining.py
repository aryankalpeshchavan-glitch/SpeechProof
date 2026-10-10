import os
for x in ['t4_localisation', 't5_invariance', 't6_human_agreement', 't7_variance', 't8_mdc95', 't9_gaming', 'ablations']:
    os.system(f'python eval/{x}.py')
