# Task 3 — Subjective Answers

**Roll No: 26210053**

---

### Q1. For each image and each stddev, the minimum alpha at which a QR scanner can extract the roll number. In which cases did the scanner fail?

I tested decoding with `cv2.QRCodeDetector` instead of judging by eye, since a recovered mark can look like a fine QR code and still not decode. The script is `qr_threshold_check.py`, which repeats the loops of `task3.py` under the same `np.random.seed(0)`, so these numbers match the saved plots. Image order is the sorted `imgs/*.jpg` order: Image 1 = hawk, Image 2 = tree, Image 3 = skier.

| stddev | Image 1 (hawk) | Image 2 (tree) | Image 3 (skier) |
| --- | --- | --- | --- |
| 0.01 | 0.01 | 0.01 | 0.01 |
| 0.05 | 0.10 | 0.10 | 0.05 |
| 0.10 | 0.20 | 0.20 | 0.15 |
| 0.15 | failed | 0.45 | failed |

**Where it failed:** Image 1 and Image 3 at stddev = 0.15 never decoded at any alpha. Image 2 was the only one to survive that noise level, and only at alpha = 0.45 — at that strength the photo is down around 13 dB and the mark is obvious, so it is not a real success.

A few things I noticed:

**The threshold climbs fast:** 0.01, then 0.10, then 0.20, then basically never. Each step up in noise roughly doubles the alpha needed, and that cost shows up as visible damage to the photo. Even the success at stddev = 0.10 needs alpha around 0.15–0.20, which is clearly visible. So the scheme really only works well for light noise.

**Decoding is not monotonic in alpha.** Image 3 at stddev = 0.05 decodes at 0.05 and 0.10 but fails at 0.15 and above. Image 1 at stddev = 0.10 decodes at 0.20, fails from 0.25 to 0.35, then decodes again at 0.40. This happens because the noise is a fresh random draw each time and clipping damage depends on image content. So the table gives the minimum alpha that worked, but a larger alpha is not guaranteed to work.

**Image 3 behaves differently from the other two.** It has the lowest thresholds at moderate noise but fails everywhere above alpha = 0.15. The skier is a bright photo with lots of sunlit snow already close to 1.0, so a large alpha pushes those pixels past the ceiling where clipping throws them away permanently — and that is exactly the information recovery needs.

---

### Q2. Key observations from `plots/task3_psnr_vs_alpha.png`

**1. The recovery curves have a peak, so there is an optimal alpha.** Every curve in the bottom row rises, peaks, and then falls. Both ends fail for different reasons. If alpha is too small, `(sigma' - sigma)` is mostly noise and then gets divided by a small number, which amplifies it. If alpha is too large, the image saturates and clipping destroys information that cannot be recovered.

**2. The peak moves right as noise increases.** A stronger attack needs a stronger embedding. This is the real answer to "find the best alpha for various s" — there isn't one best alpha, it depends on how much damage you expect.

**3. Peak height drops sharply with noise.** The best achievable recovery falls by tens of dB across the stddev range, so even at the optimal alpha the scheme degrades badly under heavy noise.

**4. Top row: the curves separate at low alpha and converge at high alpha.** At small alpha the four lines are spread out and ordered by noise level, because the error is dominated by the noise. Past about alpha = 0.3 they all collapse onto one line near 13–14 dB, because by then the distortion from the embedding itself is much larger than the noise. Beyond that, raising alpha damages the photo for no benefit.

**5. Image 3 sits well below the other two everywhere.** Same clipping reason as above. The lesson is that the right alpha depends on the image content, not just the attack.

**6. PSNR and decodability do not line up neatly.** Image 3 has the worst recovery PSNR but at stddev = 0.05 it had the best decode threshold. The peak of the PSNR curve tells you roughly where to look for a good alpha, but it is not a substitute for actually running a scanner.
