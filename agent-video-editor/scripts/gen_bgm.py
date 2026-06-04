#!/usr/bin/env python3
"""
Synthesize a simple 128 BPM sports beat as a WAV file.
Usage: python gen_bgm.py [duration_seconds] [output_path]
Default: 132s, /tmp/bgm.wav
"""
import os
import sys, wave
import numpy as np

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 132
OUTPUT   = sys.argv[2] if len(sys.argv) > 2 else "/tmp/bgm.wav"
parent = os.path.dirname(OUTPUT)
if parent:
    os.makedirs(parent, exist_ok=True)

SR  = 44100
BPM = 128
beat = SR * 60 // BPM   # samples per beat

total = SR * DURATION
buf = np.zeros(total, dtype=np.float32)

def sine(freq, dur, amp=0.5):
    t = np.linspace(0, dur/SR, dur, endpoint=False)
    return (amp * np.sin(2*np.pi*freq*t)).astype(np.float32)

def noise_burst(dur, amp=0.8):
    s = amp * (np.random.rand(dur).astype(np.float32) * 2 - 1)
    env = np.exp(-np.linspace(0, 8, dur))
    return s * env

# Drum pattern
for i in range(int(DURATION * BPM / 60) + 1):
    pos = i * beat
    if pos >= total: break
    d = min(int(SR * 0.06), total - pos)
    beat_in_bar = i % 4
    if beat_in_bar == 0:    # kick
        buf[pos:pos+d] += noise_burst(d, 0.9) * 0.8
        buf[pos:pos+d] += sine(55, d, 0.6)
    if beat_in_bar in (1, 3):  # snare
        buf[pos:pos+d] += noise_burst(d, 0.7)
    # hi-hat (every 8th note)
    for hpos in [pos, pos + beat//2]:
        if hpos < total:
            hd = min(int(SR * 0.02), total - hpos)
            buf[hpos:hpos+hd] += noise_burst(hd, 0.25) * np.random.uniform(0.6, 1.0)

# Bass line (Am: A2, C3, E3, G3)
bass_notes = [110, 110, 130.8, 110, 164.8, 164.8, 130.8, 110]
beat_half = beat // 2
for i in range(int(DURATION * BPM / 30) + 1):
    pos = i * beat_half
    if pos >= total: break
    d = min(beat_half - int(SR * 0.02), total - pos)
    freq = bass_notes[i % len(bass_notes)]
    b = sine(freq, d, 0.35)
    env = np.concatenate([
        np.linspace(0, 1, int(d*0.05)),
        np.ones(int(d*0.8)),
        np.linspace(1, 0, d - int(d*0.05) - int(d*0.8))
    ])
    buf[pos:pos+d] += b * env[:d]

# Synth pad (Am chord)
for start in range(0, total, SR * 4):
    end = min(start + SR * 4, total)
    d = end - start
    for freq in [220, 261.6, 329.6, 392]:
        buf[start:end] += sine(freq, d, 0.06)

# Fade out last 8s, or the whole track for very short placeholders.
fade_len = min(total, SR * 8)
fade_start = total - fade_len
buf[fade_start:] *= np.linspace(1, 0, fade_len)

# Normalize and write
buf = buf / max(0.01, np.abs(buf).max()) * 0.85
samples = (buf * 32767).astype(np.int16)

with wave.open(OUTPUT, 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(samples.tobytes())

print(f"BGM written: {OUTPUT} ({os.path.getsize(OUTPUT)//1024}KB, {DURATION}s, {BPM}BPM)")
