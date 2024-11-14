import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def requirement(level):
    return round(1.15 ** (level - 1) * (20000 + 20000 / 0.15) - 20000 / 0.15)

max_level = 130


plt.plot(list(range(1, max_level)), [requirement(level) for level in range(1, max_level)], label='Experience Required')


plt.xlabel('Guild Level')
plt.ylabel('Experience Required')
plt.title('Experience Requirements by Level')

ymax = round(1.15 ** (max_level - 1) * (20000 + 20000 / 0.15) - 20000 / 0.15)

plt.ylim(0, ymax)

def y_format(x, pos):
    if x >= 1_000_000_000:
        return '{:.0f}b'.format(x / 1_000_000_000)
    elif x >= 1_000_000:
        return '{:.0f}m'.format(x / 1_000_000)
    elif x >= 1_000:
        return '{:.0f}k'.format(x / 1_000)
    else:
        return '{:.0f}'.format(x)
formatter = FuncFormatter(y_format)
plt.gca().yaxis.set_major_formatter(formatter)
plt.legend()
plt.style.use('ggplot')
plt.rcParams.update({'font.size': 12, 'axes.titlesize': 16, 'axes.labelsize': 14, 'xtick.labelsize': 12, 'ytick.labelsize': 12})
plt.grid(True)
plt.show()

print("Lvl\tRequirement")
cumulative_xp = 0
cumulative_display = ""
for level in range(1, max_level):
    req = requirement(level)
    cumulative_xp += req
    xp = ""
    if req >= 1_000_000_000_000:
        xp = '{:.0f}t'.format(req / 1_000_000_000_000)
    elif req >= 1_000_000_000:
        xp = '{:.0f}b'.format(req / 1_000_000_000)
    elif req >= 1_000_000:
        xp = '{:.0f}m'.format(req / 1_000_000)
    elif req >= 1_000:
        xp = '{:.0f}k'.format(req / 1_000)
    print(f"{level}\t{req} XP or {xp}")

if cumulative_xp >= 1_000_000_000_000:
    cumulative_display = '{:.1f}t'.format(cumulative_xp / 1_000_000_000_000)
elif cumulative_xp >= 1_000_000_000:
    cumulative_display = '{:.0f}b'.format(cumulative_xp / 1_000_000_000)
elif cumulative_xp >= 1_000_000:
    cumulative_display = '{:.0f}m'.format(cumulative_xp / 1_000_000)
elif cumulative_xp >= 1_000:
    cumulative_display = '{:.0f}k'.format(cumulative_xp / 1_000)
print(f"\nCumulative xp req for 1 - {max_level-1}: {cumulative_xp} or {cumulative_display}")