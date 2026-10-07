"""Quick shaded previews of binary STL files (numpy + matplotlib, no CAD kernel needed).

usage: python3 render_stl.py out.png elev azim file1.stl[:#color] [file2.stl[:#color] ...]
"""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection


def load(path):
    with open(path, 'rb') as f:
        f.read(80)
        n = np.frombuffer(f.read(4), np.uint32)[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return d['v'].astype(float)


def main():
    out, elev, azim = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    tris, cols = [], []
    for arg in sys.argv[4:]:
        path, _, col = arg.partition(':')
        t = load(path)
        tris.append(t)
        cols += [col or '#c9c4bb'] * len(t)
    T = np.concatenate(tris)
    e, a = np.radians(elev), np.radians(azim)
    # camera: rotate about z by azim, then tilt by elev (elev 90 = top view)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.sin(e), np.cos(e)], [0, -np.cos(e), np.sin(e)]])
    P = T @ Rz.T @ Rx.T
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    light = np.array([-0.35, 0.45, 0.82])
    light /= np.linalg.norm(light)
    shade = 0.55 + 0.45 * np.clip(nrm @ light, 0, 1)
    vdir = (np.array([0, 0, 1.0]) @ Rx) @ Rz
    facing = nrm @ vdir > -1e-6
    order = np.argsort(P[:, :, 2].mean(axis=1))
    order = order[facing[order]]
    import matplotlib.colors as mc
    base = np.array([mc.to_rgb(c) for c in cols])
    fc = np.clip(base * shade[:, None], 0, 1)
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.add_collection(PolyCollection(P[order][:, :, :2], facecolors=fc[order], edgecolors=fc[order], linewidths=0.15))
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(out, dpi=140, bbox_inches='tight')


main()
