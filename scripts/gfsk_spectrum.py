import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

# ---- System parameters ----
Rb = 9600          # bit rate
sps = 16           # samples per symbol
fs = Rb * sps      # sample rate
BT = 0.35          # Gaussian BT product
h = 0.5            # modulation index
fd = h * Rb / 2    # 2400 Hz deviation
N_bits = 20000
rng = np.random.default_rng(42)

def gaussian_taps(BT, sps, span=4):
    t = np.arange(-span * sps, span * sps + 1) / sps
    alpha = np.sqrt(np.log(2) / 2) / BT
    g = (np.sqrt(np.pi) / alpha) * np.exp(-((np.pi * t / alpha) ** 2))
    return g / np.sum(g)

def gfsk_signal(bits, sps, h, BT=None):
    nrz = 2 * bits - 1
    up = np.zeros(len(nrz) * sps)
    up[::sps] = nrz
    rect = np.ones(sps) / sps
    shaped = np.convolve(up, rect, mode='same')
    if BT is not None:
        g = gaussian_taps(BT, sps)
        shaped = np.convolve(shaped, g, mode='same')
    phase = np.cumsum(shaped) * (np.pi * h)
    return np.exp(1j * phase)

bits = rng.integers(0, 2, N_bits)
gmsk = gfsk_signal(bits, sps, h, BT=BT)
plain_fsk = gfsk_signal(bits, sps, h, BT=None)

f1, P_gmsk = welch(gmsk, fs=fs, nperseg=4096, return_onesided=False)
f2, P_fsk = welch(plain_fsk, fs=fs, nperseg=4096, return_onesided=False)
f1 = np.fft.fftshift(f1); P_gmsk = np.fft.fftshift(P_gmsk)
f2 = np.fft.fftshift(f2); P_fsk = np.fft.fftshift(P_fsk)

P_gmsk_db = 10 * np.log10(P_gmsk / np.max(P_gmsk))
P_fsk_db = 10 * np.log10(P_fsk / np.max(P_fsk))

# Bandwidth markers
carson_bw = 2 * (fd + Rb)       # 24 kHz
bw_99 = 1.1 * Rb                # 10.56 kHz
bw_3db = 0.6 * Rb               # 5.76 kHz

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.plot(f2 / 1e3, P_fsk_db, color='#888', linewidth=1.3,
        label='Plain FSK (no Gaussian filter)', linestyle='--')
ax.plot(f1 / 1e3, P_gmsk_db, color='#1a3d7c', linewidth=2,
        label=f'GMSK (BT = {BT})')

ax.axvspan(-carson_bw / 2e3, carson_bw / 2e3, color='#ffd1d1', alpha=0.3,
           label=f"Carson's BW = {int(carson_bw/1000)} kHz")
ax.axvspan(-bw_99 / 2e3, bw_99 / 2e3, color='#d1f0d1', alpha=0.45,
           label=f'99% BW ≈ {bw_99/1000:.1f} kHz')

ax.axhline(-3, color='#666', linewidth=0.6, linestyle=':')
ax.axhline(-20, color='#666', linewidth=0.6, linestyle=':')
ax.axhline(-40, color='#666', linewidth=0.6, linestyle=':')
ax.text(ax.get_xlim()[1] * 0.88, -3, '-3 dB', fontsize=8, color='#444', va='bottom')
ax.text(ax.get_xlim()[1] * 0.88, -20, '-20 dB', fontsize=8, color='#444', va='bottom')
ax.text(ax.get_xlim()[1] * 0.88, -40, '-40 dB', fontsize=8, color='#444', va='bottom')

ax.set_xlim(-40, 40)
ax.set_ylim(-80, 5)
ax.set_xlabel('Frequency offset from carrier (kHz)', fontsize=11)
ax.set_ylabel('Power Spectral Density (dB, normalized)', fontsize=11)
ax.set_title(f'GMSK Frequency Spectrum  |  R$_b$ = {Rb} bps  |  '
             f'h = {h}  |  BT = {BT}  |  f$_d$ = ±{int(fd)} Hz',
             fontsize=12, color='#1a3d7c', fontweight='bold')
ax.grid(True, alpha=0.4)
ax.legend(loc='upper right', fontsize=9, framealpha=0.95)

info = (f'Center frequency: 433 MHz\n'
        f'Sample rate: {fs/1000:.0f} kHz\n'
        f'M = 2 (binary)\n'
        f'Sidelobes ~25 dB lower than\n'
        f'plain FSK thanks to Gaussian filter')
ax.text(-38, -75, info, fontsize=9, color='#333',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f4f7fb',
                  edgecolor='#1a3d7c', linewidth=1))

plt.tight_layout()
out = 'gfsk_spectrum.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f'Saved: {out}')
