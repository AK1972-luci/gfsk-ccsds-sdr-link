import numpy as np
import matplotlib.pyplot as plt

SYNC_HEX = 0xD87112BD
SYNC_LEN = 32
bits = np.array([(SYNC_HEX >> (SYNC_LEN - 1 - i)) & 1 for i in range(SYNC_LEN)])
bipolar = 2 * bits - 1

acorr = np.correlate(bipolar, bipolar, mode='full')
lags = np.arange(-SYNC_LEN + 1, SYNC_LEN)
norm = acorr / np.max(acorr)

fig, axes = plt.subplots(2, 1, figsize=(12, 7))

ax1 = axes[0]
markerline, stemlines, baseline = ax1.stem(lags, acorr, basefmt=' ')
plt.setp(markerline, color='#2a6fb5', markersize=4)
plt.setp(stemlines, color='#2a6fb5', linewidth=1.0)
ax1.axhline(0, color='black', linewidth=0.5)
ax1.set_title(f'Autocorrelation of Sync Word 0x{SYNC_HEX:08X}', fontsize=12)
ax1.set_xlabel('Shift (bits)')
ax1.set_ylabel('Correlation')
ax1.grid(True, alpha=0.4)
ax1.set_xlim(-SYNC_LEN - 2, SYNC_LEN + 2)

ax2 = axes[1]
ax2.fill_between(lags, norm, 0, color='#7eb3e0', alpha=0.5)
ax2.plot(lags, norm, color='#2a6fb5', linewidth=1.2)
ax2.axhline(0, color='black', linewidth=0.5)
ax2.set_title('Normalized Autocorrelation', fontsize=12)
ax2.set_xlabel('Shift (bits)')
ax2.set_ylabel('Normalized Correlation')
ax2.grid(True, alpha=0.4)
ax2.set_xlim(-SYNC_LEN - 2, SYNC_LEN + 2)

plt.tight_layout()
out_path = 'sync_autocorrelation_D87112BD.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f'Saved: {out_path}')
