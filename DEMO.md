# Demo Guide

This guide walks you through a complete demo of the biometric trackpad authentication system.

## Prerequisites

- Linux system with trackpad
- Python 3.7+ installed
- All dependencies installed (see [INSTALL.md](INSTALL.md))

## Demo Scenario: Signature Authentication

In this demo, we'll set up a simple signature-based authentication system.

### Step 1: Choose Your Signature Gesture

Think of a simple signature gesture you can draw on your trackpad. Good examples:
- Your initials
- A simple shape (circle, triangle, zigzag)
- A unique pattern

**Tips:**
- Keep it simple enough to reproduce consistently
- Make it complex enough to be unique
- Practice a few times before training

### Step 2: Find Your Trackpad Device

```bash
python3 trackpad_visualizer.py --list-devices
```

Look for your trackpad in the output. Example:
```
Device: ELAN0670:00 04F3:3150 Touchpad
Path: /dev/input/event14
```

Note your device path (e.g., `/dev/input/event14`).

### Step 3: Practice Mode (Optional)

Before training, practice your gesture:

```bash
python3 trackpad_visualizer.py --device /dev/input/event14
```

- Draw your gesture on the trackpad
- Press `SPACE` to capture
- Check the metrics (duration, points, path length)
- Press `C` to clear and try again
- Practice until you can draw it consistently

**Target metrics:**
- Duration: 0.5 - 3 seconds
- Points: 20+ points
- Path length: Varies by gesture

Press `Q` to quit when ready.

### Step 4: Training Phase

Now train your baseline with 10 samples:

```bash
python3 realtime_verifier_advanced.py --device /dev/input/event14 --samples 10
```

**Instructions:**
1. Draw your gesture on the trackpad
2. Press `SPACE` to capture
3. Repeat 10 times (try to be consistent!)
4. After 10 samples, baseline will be learned automatically
5. Note the baseline statistics displayed

**What to watch:**
- Duration consistency (should be similar across samples)
- Velocity CV (lower is better)
- Jerk CV (lower is better)
- Hesitation count (should be consistent)

**Example output:**
```
✓ Training sample 10/10 captured
  Duration: 1.234s (45 points)
  Path: 567px
  Velocity CV: 0.456
  Jerk CV: 0.789
  Hesitations: 2

🎓 Learning biometric baseline from 10 samples...

✓ Biometric baseline learned from 10 samples
  Duration: 1.245s ± 0.123s
  Path length: 572 ± 45 px
  Velocity CV: 0.445 ± 0.067
  Jerk CV: 0.801 ± 0.134
  Hesitations: 2.1 ± 0.9

✓ Baseline saved to baseline.pkl
```

### Step 5: Verification Phase

Now test your trained baseline:

```bash
python3 realtime_verify_with_display.py --baseline baseline.pkl --device /dev/input/event14
```

**Try these scenarios:**

#### Scenario A: Authentic Gesture (You)
1. Draw your gesture exactly as you trained it
2. Watch the real-time metrics update
3. Press `SPACE` when done
4. **Expected result:** ✓ PASS (score > 70%)

#### Scenario B: Slightly Different Gesture (You, but different)
1. Draw your gesture but slightly faster/slower
2. Press `SPACE` when done
3. **Expected result:** May pass or fail depending on difference

#### Scenario C: Completely Different Gesture (Forgery)
1. Draw a completely different shape
2. Press `SPACE` when done
3. **Expected result:** ✗ FAIL (rejected by Stage 1 Gatekeeper)

#### Scenario D: Traced Gesture (Forgery Attempt)
1. Try to carefully trace your gesture (conscious tracing)
2. Press `SPACE` when done
3. **Expected result:** ✗ FAIL (rejected by Stage 3 Dynamics - high jerk)

### Step 6: Understanding the Results

Watch the verification output:

**Successful verification:**
```
============================================================
✓ VERIFICATION PASSED
============================================================
Overall Score: 85.3%

Stage 1 (Gatekeeper): ✓ PASS
  Score: 92.1%
  Reason: passed

Stage 3 (Dynamics): ✓ PASS
  Score: 82.4%
  Reason: passed

Gesture Metrics:
  Duration: 1.267s (baseline: 1.245±0.123s)
  Velocity CV: 0.432 (baseline: 0.445±0.067)
  Jerk CV: 0.756 (baseline: 0.801±0.134)
  Hesitations: 2 (baseline: 2.1±0.9)
```

**Failed verification (wrong duration):**
```
============================================================
✗ VERIFICATION FAILED
============================================================
Overall Score: 35.2%

Stage 1 (Gatekeeper): ✗ FAIL
  Score: 45.3%
  Reason: duration_mismatch (0.543s vs 1.245±0.123s)
```

**Failed verification (traced/forged):**
```
============================================================
✗ VERIFICATION FAILED
============================================================
Overall Score: 58.7%

Stage 1 (Gatekeeper): ✓ PASS
  Score: 88.2%
  Reason: passed

Stage 3 (Dynamics): ✗ FAIL
  Score: 45.6%
  Reason: jerk_mismatch (σ=3.45)

Gesture Metrics:
  Jerk CV: 1.523 (baseline: 0.801±0.134)
```

### Step 7: Real-Time Metrics

Notice the real-time metrics panel on the right side:

**While drawing:**
- ⏱️ Duration updates live
- 📍 Point count increases
- 📏 Path length grows
- 🏃 Velocity CV calculated
- ⚡ Jerk CV calculated (CRITICAL)
- ⏸️ Hesitations detected
- 📊 Live verification scores

**Key insight:** Watch the Jerk CV! If you're tracing consciously, it will be much higher than your baseline.

## Advanced Demo: Multi-Sample Testing

Test with multiple attempts:

```bash
# Train with more samples for better accuracy
python3 realtime_verifier_advanced.py --device /dev/input/event14 --samples 20

# Verify multiple times
python3 realtime_verify_with_display.py --baseline baseline.pkl --device /dev/input/event14
```

Try 10 verification attempts:
- 5 authentic (you drawing normally)
- 5 forgeries (different gestures or traced)

**Expected results:**
- Authentic: 80-100% pass rate
- Forgeries: 0-20% pass rate

## Demo Tips

### For Best Results:
1. **Practice first** - Get comfortable with your gesture
2. **Be consistent** - Draw the same way each time during training
3. **Natural speed** - Don't rush or go too slow
4. **Relaxed** - Draw naturally, not consciously

### Common Issues:
- **Low pass rate on authentic gestures:** Retrain with more samples (--samples 20)
- **High pass rate on forgeries:** Your gesture may be too simple
- **Gestures skipped:** Draw slower or longer paths

### Interesting Experiments:
1. **Time of day:** Does your gesture change when tired?
2. **Hand position:** Does it matter where you place your hand?
3. **Speed variation:** How much can you vary speed and still pass?
4. **Other people:** Can someone else pass by watching you?

## Demo Video Script

If you want to record a demo video:

1. **Introduction (30s)**
   - Show the project README
   - Explain what it does

2. **Training Phase (2 min)**
   - Show device detection
   - Draw gesture 10 times
   - Show baseline learning

3. **Verification Phase (3 min)**
   - Authentic gesture → PASS
   - Different gesture → FAIL
   - Traced gesture → FAIL (highlight jerk metric)
   - Show real-time metrics

4. **Conclusion (30s)**
   - Summarize results
   - Mention limitations and future work

## Next Steps

After the demo:
- Read the [full documentation](README.md)
- Explore the [code](advanced_biometrics.py)
- Try different gestures
- Experiment with parameters
- Contribute improvements!

## Questions?

Check the [troubleshooting guide](README.md#-troubleshooting) or open an issue on GitHub.

---

**Happy authenticating! 🔐**
