# GFSK CCSDS SDR Link — USRP B200 → HackRF One

A complete, working software-defined radio telemetry link built in GNU Radio 3.10 for
CubeSat ground-segment testing. It sends CCSDS-framed telemetry over 433 MHz GFSK from a
USRP B200 and recovers it on a HackRF One, with forward error correction and frame
synchronisation matching the CCSDS 131.0-B-3 recommendation.

Built for the STeRG (Space Technology Research Group, MIT-WPU) 3U CubeSat programme
as the bench prototype of the flight comms subsystem.

```
TX  telemetry (223 B) → RS(255,223) → conv. r=1/2 k=7 → ASM 0x1ACFFC1D → GFSK (BT 0.35) → USRP B200
                                        ~~~ 433 MHz, 500 kbaud, h = 0.5 ~~~
RX  HackRF One → IQ correct → AGC → LPF → quad demod → DC block → symbol sync → ASM correlate → Viterbi → RS
```

## Results (bench, indoor)

| Metric | Value |
|---|---|
| Frame sync acquisition | reliable on every frame |
| Viterbi decode | 255 B / frame |
| Byte accuracy after decode | 96 %+ (214 / 223 bytes) |
| Symbol rate | 500 kbaud |
| Deviation / mod. index | 125 kHz / 0.5 |

Recovered stream:

```
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
```

## Why it is built this way

* **Custom demod chain instead of `digital_gfsk_demod`**: the stock hierarchical block
  hides the clock-recovery and AGC parameters that need tuning on real hardware. The
  explicit chain exposes every knob. See `docs/DESIGN.md` §6.
* **ASM prepend in an embedded Python block**: `tagged_stream_mux` drops tags through
  the FEC chain in 3.10; a 20-line Python block is deterministic and debuggable.
* **CCSDS framing from day one**: the same frames drop straight into cFS on the flight
  side and OpenC3 COSMOS on the ground side without re-encoding. §7 of the design
  doc covers the UDP/ZMQ swap-in.

## Repository layout

```
flowgraphs/   gfsk_tx.grc, gfsk_rx.grc (+ generated .py)   GNU Radio Companion files
scripts/      gfsk_spectrum.py        Welch PSD of the transmitted signal
              asm_autocorrelation.py  sync-word autocorrelation plot
docs/         DESIGN.md               full design notes, formulas, troubleshooting
```

## Requirements

* GNU Radio 3.10.x with `gr-uhd`, `gr-osmosdr` (HackRF) and `gr-satellites`
* Python 3.10+, NumPy, SciPy, Matplotlib (for `scripts/`)
* Hardware: USRP B200 (TX) and HackRF One (RX), any 433 MHz antennas, USB 3.0 port for the B200

## Run

```bash
# TX (USRP B200)
gnuradio-companion flowgraphs/gfsk_tx.grc      # or: python3 flowgraphs/gfsk_tx.py

# RX (HackRF One)
gnuradio-companion flowgraphs/gfsk_rx.grc
# decoded frames land in gfsk_rx_output.txt in the working directory
```

Start with TX gain around 40 dB and HackRF RF/IF/BB gains at 42/32/30 dB for a bench test
under one metre, then back off if the constellation saturates.

## Known limitations / next steps

* RS decoder currently strips parity only; full RS error correction is the next step.
* No Doppler tracking yet, so this is a bench and short-range link, not a LEO pass receiver.
* BER counter and link-budget calculator are planned. See `docs/DESIGN.md` §11.

## Author

Aman Kumar Gupta, B.Tech Electronics & Telecommunication, MIT-WPU Pune.
Comms subsystem, STeRG CubeSat programme.
[GitHub](https://github.com/AK1972-luci)

## Licence

GPL-3.0, matching the GNU Radio generated sources.
