"""Debug: plot each symbol in isolation to see what they look like."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import matplotlib.pyplot as plt

lib = json.load(open('normalized_library.json'))
symbols = ['(', ')', '{', '}', '%']

fig, axes = plt.subplots(1, len(symbols), figsize=(15, 4))
for ax, sym in zip(axes, symbols):
    data = lib[sym]
    for stroke in data['strokes']:
        xs = [p[0] for p in stroke]
        ys = [p[1] for p in stroke]
        ax.plot(xs, ys, 'b-', linewidth=1.5)
        ax.plot(xs[0], ys[0], 'go', markersize=4)   # start = green
        ax.plot(xs[-1], ys[-1], 'ro', markersize=4)  # end = red
    ax.set_title(f"'{sym}'  w={data['width']}", fontsize=12)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
