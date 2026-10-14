# Task 4 — Subjective Answers

**Roll No: 26210053**

---

### Q1. For each image and each quality factor, the minimum alpha at which a QR scanner can extract the roll number.

Same method as Task 3 — decoding tested with `cv2.QRCodeDetector` via `qr_threshold_check.py`, which repeats the loops of `task4.py`. Image 1 = hawk, Image 2 = tree, Image 3 = skier.

| Quality | Image 1 (hawk) | Image 2 (tree) | Image 3 (skier) |
| --- | --- | --- | --- |
| 90 | 0.01 | 0.01 | 0.05 |
| 70 | 0.05 | 0.05 | 0.05 |
| 50 | 0.05 | 0.05 | 0.05 |
| 30 | 0.01 | 0.05 | 0.05 |

**There were no failures at all here.** Every image decoded at every quality factor, and alpha = 0.05 was enough in every case. That is the main result: JPEG compression at these quality levels is a much gentler attack than Gaussian noise was.

Things I noticed:

- **The thresholds barely move.** Going from quality 90 down to quality 30 changes the required alpha by at most one step. In Task 3 the same span of attack strength went from 0.01 to complete failure.
- **alpha = 0.05 is actually usable.** At that strength the watermarked photo sits around 29–30 dB and looks identical to the original, but the roll number still decodes after a quality-30 JPEG round trip for all three images.
- **The single decode of Image 1 at quality 30, alpha = 0.01 is not a real trend.** It fails at quality 70 and 50 at that alpha but works at 30. alpha = 0.01 is right at the edge of viability everywhere, so whether a case lands just inside or outside is basically down to how the quantisation rounds. The dependable threshold is 0.05.
- **Image 3 fails at high alpha again.** It decodes at 0.05 for every quality but fails above alpha = 0.10 or 0.20. That is not a compression effect at all — it is the same bright-snow clipping from Task 3. The attack is not what breaks Image 3, the embedding is.

**Why JPEG is so much kinder than noise:** JPEG throws away information mainly in the high-frequency detail, which is the small singular values. Our watermark is added to the top singular values, which is exactly what compression is designed to preserve. Gaussian noise is spread across the whole spectrum and hits the leading components directly, which is why it does more damage. This is the practical payoff of the choice explained in Task 1 Q2.

---

### Q2. Key observations from `plots/task4_psnr_vs_alpha.png`

**1. Same peaked shape as Task 3, but the peak is further left.** The peaks land around alpha = 0.05 to 0.15, compared with 0.10 to 0.20 under noise. A weaker attack needs a weaker embedding, so the optimum shifts toward better invisibility. The two failure modes are the same: too small an alpha and the compression artefacts swamp `(sigma' - sigma)` before it is divided by a tiny number; too large and clipping destroys information.

**2. The quality curves are bunched close together.** This is the clearest contrast with Task 3, where the four stddev curves were widely separated and peak recovery collapsed by tens of dB. Here the four curves for a given image sit almost on top of each other, only a couple of dB apart. Dropping JPEG quality from 90 to 30 costs much less than raising stddev from 0.01 to 0.05.

**3. Past about alpha = 0.25 all four quality curves merge into one.** Beyond that point the quality factor stops mattering — the dominant error is the clipping from embedding, not the compression. Raising alpha further just damages the photo for nothing.

**4. Top row: quality only matters at small alpha.** The curves separate clearly at alpha = 0.01 (about 43 dB at q=90 versus 32 dB at q=30 for Image 1) and converge by around alpha = 0.2. Once the embedding distortion is large, the compression loss on top is negligible by comparison.

**5. There is a real usable window here, which Task 3 did not have.** Reading the plots with the decode table, alpha around 0.05 is at or near the peak of the recovery curve, keeps the photo near 29–30 dB, and decodes for all three images at every quality down to 30. Under Gaussian noise, surviving stddev 0.10 already needed alpha around 0.15–0.20, which visibly damages the photo. So the scheme is genuinely robust to re-encoding but only weakly robust to noise.

**6. Image 3 is the weakest carrier in both tasks.** Its recovery curve is lowest at every alpha and every quality, and it is the one that fails at high alpha. Since that failure looks the same under both noise and compression, the cause is the cover content, not the attack. That supports the Task 3 conclusion that alpha should be chosen per image.
