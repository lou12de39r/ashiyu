"""Run the v19 layout script and freeze its geometry to layout_v20.json (mm, origin = rear-left corner, y towards the user)."""
import json, runpy, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
g = runpy.run_path('layout_v20.py')
PX, PY, M, WEDGE = g['PX'], g['PY'], g['M'], g['WEDGE']
out = {'units': 'mm', 'origin': 'rear-left corner of the case outline, +x right, +y towards the user',
       'pitch': [PX, PY], 'outline': [round(g['W'], 3), round(g['H'], 3)], 'keys': []}
for i, (xu, yu, t, kind, w, h) in enumerate(g['keys']):
    cx = M + (xu + w / 2) * PX; cy = WEDGE + (yu + h / 2) * PY
    out['keys'].append({'id': i, 'label': t.replace('\n', ' '), 'kind': kind, 'cx': round(cx, 3), 'cy': round(cy, 3),
                        'w_u': w, 'h_u': h, 'rot_deg': g['ROT'].get(i, 0.0)})
tx, ty = g['tx'], g['ty']
out['trackpad'] = {'x': round(tx, 3), 'y': round(ty, 3), 'w': g['TPW'], 'h': round(g['TPH'], 3)}
LY = g['LY']
out['leds'] = [{'name': f'BT{i+1}', 'cx': round(M + 0.5 * PX + 4 + 4.5 * i, 3), 'cy': round(LY, 3), 'color': 'green'} for i in range(3)]
out['leds'] += [{'name': 'PWR', 'cx': round(g['W'] - 8, 3), 'cy': round(LY, 3), 'color': 'green/red bicolor'},
                {'name': 'CHG', 'cx': round(g['W'] - 14, 3), 'cy': round(LY, 3), 'color': 'orange'}]
out['usb_c'] = {'x': round(tx + 4, 3), 'y': -1.0, 'w': 9.0, 'h': 7.3, 'note': 'mid-mount, opening in the rear edge'}
out['module'] = {'x': round(tx + 19, 3), 'y': 0.3, 'w': 10.5, 'h': 15.5, 'note': 'MDBT50Q-1MV2, antenna at the rear edge'}
json.dump(out, open('layout_v20.json', 'w'), ensure_ascii=False, indent=1)
print(len(out['keys']), 'keys', out['outline'], out['trackpad'])
