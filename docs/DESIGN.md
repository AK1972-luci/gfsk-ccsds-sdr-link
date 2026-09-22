# GFSK SDR-to-SDR Communication System Documentation

## Author: Aman Kumar Gupta
## Date: March 2026
## Hardware: USRP B200 (TX) + HackRF One (RX)

---

## 1. System Overview

This system implements a complete GFSK (Gaussian Frequency Shift Keying) communication link using Software Defined Radios, with CCSDS-standard forward error correction and frame synchronization. It is designed to be compatible with cFS (core Flight System) and OpenC3/MCC ground station for future CubeSat (3U-SAT-01) operations.

### System Block Diagram

```
TX (USRP B200):
  Telemetry Data (223 bytes)
       |
       v
  RS(255,223) Encoder ---> Conv. Encoder (r=1/2, k=7) ---> Pack Bits
       |
       v
  ASM Prepend (0x1ACFFC1D) ---> GFSK Modulator ---> USRP B200 TX
       |
       v
  ~~~~~~~~~ 433 MHz RF Channel ~~~~~~~~~
       |
       v
RX (HackRF One):
  HackRF RX ---> DC Fix ---> AGC ---> Low Pass Filter
       |
       v
  Quadrature Demod ---> DC Blocker ---> Symbol Sync (Clock Recovery)
       |
       v
  CCSDS Frame Sync (ASM Correlation) ---> Viterbi Decoder ---> RS Decoder
       |
       v
  Decoded Telemetry Data (223 bytes)
```

---

## 2. System Parameters

| Parameter | Value | Formula / Notes |
|-----------|-------|-----------------|
| Sample Rate (fs) | 2 MHz | Set by USRP/HackRF capability |
| Samples Per Symbol (sps) | 4 | Oversampling factor |
| Symbol/Baud Rate (Rb) | 500 kbaud | Rb = fs / sps = 2M / 4 |
| Bit Rate | 500 kbps | Same as baud rate for binary FSK |
| Center Frequency (fc) | 433 MHz | ISM band |
| FSK Deviation (fd) | 125 kHz | fd = h x Rb / 2 |
| Modulation Index (h) | 0.5 | h = 2 x fd / Rb = 2 x 125k / 500k |
| Gaussian BT product | 0.35 | Bandwidth-time product for pulse shaping |
| GFSK Sensitivity | 0.3927 rad/sample | 2*pi*fd/fs = 2*pi*125k/2M |

---

## 3. Key Formulas

### 3.1 GFSK Modulation

**Modulation Index:**
```
h = 2 * fd / Rb
h = 2 * 125,000 / 500,000 = 0.5
```
- h = 0.5 is the minimum for orthogonal FSK (MSK-like), giving optimal spectral efficiency.

**GFSK Sensitivity (radians per sample):**
```
sensitivity = 2 * pi * fd / fs
            = 2 * pi * 125,000 / 2,000,000
            = 0.3927 rad/sample
```
This is the phase change per sample for the maximum frequency deviation.

**Gaussian Filter BT Product:**
```
BT = 0.35
```
- Controls the bandwidth of the Gaussian pulse shaping filter.
- Lower BT = narrower bandwidth, more ISI (inter-symbol interference).
- BT = 0.35 is standard for Bluetooth and many satellite links.
- The Gaussian filter smooths abrupt frequency transitions, reducing spectral splatter.

**Occupied Bandwidth (Carson's Rule for GFSK):**
```
BW = 2 * (fd + Rb) = 2 * (125k + 500k) = 1.25 MHz
```
With Gaussian shaping (BT=0.35), actual occupied BW is narrower (~600 kHz at -20 dB).

### 3.2 Quadrature Demodulation (FM Discriminator)

**Demod Gain:**
```
gain = fs / (2 * pi * fd)
     = 2,000,000 / (2 * pi * 125,000)
     = 2.546
```
This normalizes the demodulator output so that +fd maps to +1.0 and -fd maps to -1.0.

**How it works:**
The quadrature demodulator computes the instantaneous frequency of the complex baseband signal:
```
f_inst(n) = angle( x(n) * conj(x(n-1)) ) / (2*pi*Ts)
```
where:
- x(n) is the complex baseband sample
- Ts = 1/fs is the sample period
- The output is proportional to the instantaneous frequency deviation

For GFSK, the output swings between approximately +1 (bit=1) and -1 (bit=0) after proper gain scaling.

### 3.3 Symbol Synchronization (Clock Recovery)

**Mueller-Muller Timing Error Detector (MM-TED):**
```
e(n) = x(n) * d(n-1) - x(n-1) * d(n)
```
where:
- x(n) = current sample at optimal timing
- d(n) = decision (hard slice of x(n))
- e(n) = timing error estimate

**Loop Parameters:**
```
Loop Bandwidth (BW_loop) = 0.030
Damping Factor (zeta)    = 1.414 (critically damped)
Max Deviation            = 0.5 symbols
```

**Why Mueller-Muller for GFSK?**
- MM-TED works on the signal AFTER matched filtering
- Does not require a transition for every symbol (unlike Gardner TED)
- Optimal for binary modulations like FSK/GFSK where data-aided timing works well

### 3.4 Forward Error Correction

**Reed-Solomon RS(255,223):**
```
Input:  223 data bytes
Output: 255 bytes (223 data + 32 parity)
Code Rate: 223/255 = 0.875
Symbol Size: 8 bits (GF(2^8))
Error Correction: t = (255-223)/2 = 16 symbol errors
```
- Can correct up to 16 byte errors per frame
- CCSDS standard for space communications

**Convolutional Code (r=1/2, k=7):**
```
Rate: 1/2 (each input bit produces 2 output bits)
Constraint Length: k = 7 (6 memory elements)
Generator Polynomials: g1 = 1111001 (0x79), g2 = 1011011 (0x5B)
Free Distance: d_free = 10
```
- Doubles the bitstream: 255 bytes x 8 bits x 2 = 4080 coded bits
- Decoded by Viterbi algorithm (maximum likelihood decoding)

**Combined Coding Gain:**
```
Concatenated Code: RS(255,223) outer + Conv(r=1/2, k=7) inner
Overall Code Rate: 0.875 * 0.5 = 0.4375
Coding Gain (soft Viterbi): ~7-8 dB at BER = 10^-5
```

### 3.5 Frame Structure

```
|<-- 4 bytes -->|<------------ 510 bytes ------------>|
|    ASM        |         Encoded Data                 |
| 0x1ACFFC1D    | Conv(RS(223 data + 32 parity))       |
|               | = 255 bytes * 8 * 2 / 8 = 510 bytes |
|<----------------- 514 bytes total ------------------>|
```

**CCSDS Attached Sync Marker (ASM):**
```
ASM = 0x1ACFFC1D
Binary: 00011010 11001111 11111100 00011101
```
- 32-bit pattern used by CCSDS for frame synchronization
- Same sync marker used by cFS and OpenC3
- Autocorrelation properties make it detectable even in noisy channels

---

## 4. TX Chain — Detailed Description

### 4.1 Data Source
```
Data: "ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F\n"
Size: 47 bytes, repeated to fill 223-byte RS frame
```

### 4.2 RS(255,223) Encoder
- Input: 223 bytes (vector)
- Output: 255 bytes (vector) — adds 32 parity bytes
- Standard: CCSDS 131.0-B-3
- Can correct up to 16 byte errors at the receiver

### 4.3 Convolutional Encoder (CCSDS r=1/2, k=7)
- Input: 255 bytes (as unpacked bits from vector-to-stream)
- Output: 4080 unpacked bits (each input bit produces 2 output bits)
- After packing (8 bits per byte): 510 bytes

### 4.4 ASM Prepend (Embedded Python Block)
- Collects 510 encoded bytes per frame
- Prepends 4-byte CCSDS ASM (0x1ACFFC1D)
- Output: 514 bytes per frame
- This is done in an Embedded Python Block because GNU Radio's `tagged_stream_mux` has tag propagation issues

### 4.5 GFSK Modulator
- `do_unpack: True` — unpacks each byte to 8 bits before modulating
- Applies Gaussian pulse shaping (BT = 0.35) to the NRZ data
- Generates complex baseband FM signal with deviation = 125 kHz
- Output rate: samp_rate = 2 MHz (sps=4 samples per symbol)

### 4.6 USRP B200 Sink
- Antenna: TX/RX port
- Center Frequency: 433 MHz
- Sample Rate: 2 MHz
- Gain: 0-89 dB (adjustable via GUI slider)

---

## 5. RX Chain — Detailed Description

### 5.1 HackRF Source (osmosdr)
- Antenna: RX input
- Center Frequency: 433 MHz
- Sample Rate: 2 MHz
- Three gain stages (all adjustable via GUI):
  - RF Gain: 0-62 dB (step 14 dB)
  - IF Gain: 0-40 dB (step 8 dB)
  - BB Gain: 0-62 dB (step 2 dB)

### 5.2 DC Offset Removal (blocks_correctiq)
- HackRF has a known DC offset (spike at center frequency)
- This block estimates and removes the DC component
- Essential for accurate demodulation

### 5.3 AGC (Automatic Gain Control)
```
Attack Rate:  0.1  (fast response to signal increase)
Decay Rate:   0.01 (slow response to signal decrease)
Reference:    1.0  (target output level)
Max Gain:     65536
```
- Normalizes signal amplitude regardless of distance/path loss
- Ensures consistent input level to the demodulator
- Prevents both signal clipping and weak signal loss

### 5.4 Low Pass Filter
```
Type:       FIR (Hamming window)
Cutoff:     200 kHz
Transition: 50 kHz
Decimation: 1 (no rate change)
```
- Isolates the GFSK signal (BW ~ 600 kHz)
- Rejects adjacent channel interference and out-of-band noise
- Improves SNR before demodulation

### 5.5 Quadrature Demodulator (FM Discriminator)
```
Gain = fs / (2*pi*fd) = 2,000,000 / (2*pi*125,000) = 2.546
```
- Converts complex baseband signal to real-valued frequency deviation
- Output: float stream swinging between +1 (bit 1) and -1 (bit 0)
- This is the standard non-coherent demodulation approach for FSK/GFSK

### 5.6 DC Blocker
```
Length: 32 samples
Type: long form (IIR-based)
```
- Removes any residual DC offset from the demodulated signal
- Ensures the decision threshold is centered at zero
- Critical for correct bit slicing

### 5.7 Symbol Synchronization (Clock Recovery)
```
TED Type:     Mueller-Muller
Loop BW:      0.030
Damping:      1.414 (critically damped)
Max Dev:      0.5 symbols
Resampler:    MMSE 8-tap (polyphase filterbank, 128 filters)
Output SPS:   1 (one sample per symbol)
```
- Recovers symbol timing from the demodulated signal
- Outputs exactly one soft float sample per symbol at the optimal sampling instant
- Mueller-Muller TED is optimal for binary modulations

### 5.8 CCSDS Frame Sync (Embedded Python Block)
```
ASM Pattern:  0x1ACFFC1D (32 bits)
Threshold:    5 bit errors allowed
Frame Size:   4080 soft bits per frame
```
**Algorithm:**
1. Buffer incoming soft float samples
2. At each position, hard-slice 32 samples and correlate with ASM pattern
3. If correlation >= 27/32 (threshold = 5 errors), ASM found
4. Extract next 4080 soft samples (the encoded frame)
5. Output to Viterbi decoder
6. If no match, advance by 1 sample and try again

### 5.9 Viterbi Decoder (fec_decode_ccsds_27_fb)
- Input: 4080 soft floats (conv-encoded bits)
- Output: 255 bytes (RS-encoded frame)
- Algorithm: Maximum likelihood (Viterbi) decoding
- Soft-decision input provides ~2 dB gain over hard-decision

**Why soft-decision is important:**
```
Hard decision: input is 0 or 1 → BER improvement ~5 dB
Soft decision: input is -1.0 to +1.0 → BER improvement ~7-8 dB
Difference: ~2-3 dB coding gain advantage for soft-decision
```

### 5.10 RS Decoder (Embedded Python Block)
- Input: 255 bytes per frame from Viterbi
- Skips first 4 bytes (Viterbi tail/flush bytes)
- Extracts 223 data bytes
- Output: Clean telemetry data

---

## 6. Why We Don't Use the Built-in `digital_gfsk_demod` Block

This is a critical design decision. Here's why we use Quadrature Demod + Symbol Sync instead:

### 6.1 Soft-Decision Decoding (Most Important Reason)
```
digital_gfsk_demod → outputs HARD bits (0 or 1)
Quadrature Demod + Symbol Sync → outputs SOFT floats (-1.0 to +1.0)
```
- Our Viterbi decoder (`fec_decode_ccsds_27_fb`) requires **soft float inputs**
- Soft decisions preserve confidence information (e.g., 0.95 means "very likely a 1", 0.12 means "barely a 1")
- This gives **2-3 dB coding gain** over hard decisions — equivalent to doubling TX power!
- `digital_gfsk_demod` hard-slices internally, destroying this information

### 6.2 Frame Synchronization in Soft Domain
- Our CCSDS frame sync searches for ASM (0x1ACFFC1D) in the **soft float stream**
- This allows correlation-based detection with configurable error threshold
- More robust in noisy channels than searching for ASM in hard-sliced bits
- `digital_gfsk_demod` would require a separate hard-bit correlator (less reliable)

### 6.3 Timing Error Detector (TED) Choice
```
Custom Symbol Sync:      Mueller-Muller TED (optimal for FSK/GFSK)
digital_gfsk_demod:      May use a different TED internally (often Gardner, optimized for PSK)
```
- Mueller-Muller TED works on post-filter samples and is data-aided
- We can tune loop_bw (0.030) and damping (1.414) specifically for our link

### 6.4 Debugging & Observability
- Custom chain allows monitoring at every stage:
  - Raw spectrum (before demod)
  - Demod signal shape (after quad demod, before clock recovery)
  - Recovered symbols (after symbol sync)
- `digital_gfsk_demod` is a black box — no intermediate signals to observe
- This was essential during development to identify and fix issues

### 6.5 Channel Impairment Handling
- Custom chain allows inserting AGC, DC blocker, and adaptive blocks between stages
- `digital_gfsk_demod` has fixed internal processing — no room for channel-specific corrections
- HackRF has known DC offset issues that require explicit correction before demod

### 6.6 Summary Comparison

| Feature | Custom Chain | digital_gfsk_demod |
|---------|-------------|-------------------|
| Output Type | Soft floats | Hard bits |
| Viterbi Coding Gain | ~7-8 dB | ~5 dB |
| TED | Mueller-Muller (FSK-optimized) | Internal (unknown) |
| Frame Sync | Soft correlation | Hard-bit search |
| Intermediate Monitoring | Yes (4 plots) | No |
| DC Offset Handling | Explicit blocks | None |
| AGC Integration | Before demod | N/A |
| Extensibility | High (modular) | Low (monolithic) |

---

## 7. cFS and MCC/OpenC3 Compatibility

### 7.1 Will This Work with cFS?

**Yes.** This system is designed for CCSDS compatibility:

| Feature | Our System | cFS Standard |
|---------|-----------|--------------|
| Frame Sync (ASM) | 0x1ACFFC1D | 0x1ACFFC1D (CCSDS standard) |
| Reed-Solomon | RS(255,223) | RS(255,223) (CCSDS 131.0-B-3) |
| Conv. Code | r=1/2, k=7 | r=1/2, k=7 (CCSDS 131.0-B-3) |
| Frame Size | 223 data bytes | Configurable (223 is standard) |

### 7.2 What Needs to Change for cFS Integration

**TX Side (Flight Software → USRP):**
1. Replace `blocks_vector_source` (test data) with a **ZMQ or UDP source** that receives CCSDS packets from cFS
2. cFS Software Bus (SB) sends telemetry packets → cFS IO adapter → UDP/ZMQ → GNU Radio TX
3. The encoding chain (RS → Conv → ASM → GFSK) stays exactly the same
4. cFS packets already include CCSDS primary/secondary headers

**RX Side (HackRF → MCC/OpenC3):**
1. Replace `blocks_file_sink` with a **ZMQ or UDP sink** that sends decoded data to OpenC3
2. The demod/decode chain stays exactly the same
3. OpenC3 COSMOS receives the 223-byte frames and parses CCSDS headers
4. Add a **CCSDS packet router** (optional) to separate telemetry by APID

### 7.3 CCSDS Packet Structure (for reference)

```
|<--- 6 bytes --->|<--- N bytes --->|
| Primary Header  |    Payload      |
|                 |                 |
| Version (3b)    |                 |
| Type (1b)       |                 |
| Sec Hdr (1b)    |                 |
| APID (11b)      |                 |
| Seq Flags (2b)  |                 |
| Seq Count (14b) |                 |
| Length (16b)     |                 |
```

cFS wraps telemetry in CCSDS packets. Our system transports these packets transparently inside the 223-byte RS data field.

### 7.4 Integration Architecture

```
FLIGHT SIDE:
  cFS App → Software Bus → IO Adapter → UDP → GNU Radio TX → USRP B200 → Antenna
                                                    |
                                         [RS + Conv + ASM + GFSK]

  ~~~~~~~~~~~~~~~~~~~ 433 MHz RF Link ~~~~~~~~~~~~~~~~~~~

GROUND SIDE:
  Antenna → HackRF → GNU Radio RX → UDP → OpenC3 COSMOS → MCC Display
                          |
               [GFSK Demod + Frame Sync +
                Viterbi + RS Decode]
```

---

## 8. Test Results

### 8.1 Test Configuration
- TX: USRP B200, 433 MHz, 2 MSPS, Gain 40 dB
- RX: HackRF One, 433 MHz, 2 MSPS, RF=42 dB, IF=32 dB, BB=30 dB
- Distance: Indoor bench test (< 1 meter)
- Data: `ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F`

### 8.2 Results
- Frame sync acquisition: Successful (ASM detected reliably)
- Viterbi decoding: Successful (255 bytes per frame)
- RS parity stripping: Successful (223 clean data bytes)
- Data integrity: **96%+ byte accuracy** (214/223 bytes correct per frame)
- Received data confirmed:
```
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
ID:0000 SAT:3U-SAT-01 T:15:25:41 BAT:98% GPS:F
```

---

## 9. File Locations

| File | Path | Purpose |
|------|------|---------|
| TX Flowgraph | `flowgraphs/gfsk_tx.grc` | GFSK Transmitter for USRP B200 |
| RX Flowgraph | `flowgraphs/gfsk_rx.grc` | GFSK Receiver for HackRF |
| RX Output | `gfsk_rx_output.txt` (working dir) | Decoded telemetry data |

---

## 10. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `tagged_stream_mux` error | Tag propagation through encoding chain | Use Embedded Python Block for ASM prepend (already fixed) |
| Empty output file | File path on OneDrive (sync issues) | Write output outside any cloud-synced folder |
| Garbled data | No frame sync / wrong alignment | Added CCSDS ASM correlation (already fixed) |
| 4 garbage bytes at frame start | Viterbi tail bits | RS decoder skips first 4 bytes (already fixed) |
| DC spike in spectrum | HackRF hardware DC offset | Added `blocks_correctiq` + `dc_blocker` |
| Weak signal | Insufficient gain | Adjust RF/IF/BB gain sliders; added AGC |
| USB 2.0 warning | USRP on USB 2.0 port | Use USB 3.0 port for full bandwidth |
| Buffer allocation warnings | Non-power-of-2 vector sizes (223, 255) | Harmless warnings, ignore |

---

## 11. Future Enhancements

1. **cFS Integration**: Replace test data source with UDP/ZMQ from cFS Software Bus
2. **OpenC3 Integration**: Replace file sink with UDP/ZMQ to OpenC3 COSMOS
3. **Full RS Error Correction**: Add proper RS decode library (currently strips parity only)
4. **BER Measurement**: Add bit error rate counter for link quality assessment
5. **Doppler Compensation**: Add frequency offset tracking for LEO satellite pass
6. **Link Budget**: Calculate required TX power and antenna gain for actual orbital distance
7. **Two-way Link**: Add command uplink (ground → satellite) path
