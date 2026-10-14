# Task 2 — Subjective Answers

**Roll No: 26210053**

---

### Q1. What do you think PSNR is measuring? What could be a disadvantage of it?

PSNR measures how similar two images are, pixel by pixel. Underneath it is just the mean squared error:

```
MSE  = (1/N) * sum over all pixels and channels of (I_ref(p) - I(p))^2
PSNR = 20 * log10( MAX / sqrt(MSE) )
```

It is the ratio between the largest possible pixel value (MAX = 1, since our images are in [0,1]) and the typical error, in decibels. Higher means more similar, and identical images give infinity. I use it two ways here: `PSNR(C, C_alpha)` for invisibility, and `PSNR(Q, Q_recovered)` for recoverability.

The main disadvantage is that PSNR does not know what an image is. It treats the picture as a bag of numbers, so:

- It ignores **where** the error is. The same total error spread evenly across the frame or concentrated in one ugly blotch on the subject's face gives the same PSNR, even though one is invisible and the other ruins the photo.
- It does not match human vision. A small uniform brightness shift is harmless to look at but tanks the PSNR, while structured artefacts like banding or blocking can leave PSNR looking fine and still be obvious.

The disadvantage that actually affected me in this assignment is more specific: **PSNR does not measure what I care about.** What I need is a yes/no answer — can a scanner read `26210053`? PSNR is a poor proxy. Several of my recovered QR codes had a colour cast that dragged their PSNR down to around 12–18 dB, but they decoded perfectly, because a QR reader binarises the image and has error correction and does not care about a tint. Image 3 had the worst recovery PSNR of the three but sometimes the best decode threshold. So picking alpha by PSNR alone would have given the wrong answer, and I had to run an actual decoder instead.

---

### Q2. Briefly explain what the script `task2.py` is doing.

`task2.py` replaces the hard-coded alpha from Task 1 with a value I can choose based on evidence. It does this by sweeping alpha and measuring both sides of the trade-off.

What it does:

1. Loads the three cover photos as RGB floats in [0,1], loads my QR using the path from `.env`, and resizes the QR to 321x321 so its spectrum matches each cover's k = 321.
2. Defines `compute_psnr`, which I implemented as the MSE averaged over every pixel and channel (N = H x W x 3), converted to dB with MAX = 1, returning infinity if the images are identical.
3. Loops over eleven alpha values from 0.01 to 0.5. For each alpha and each image it embeds the QR, immediately recovers it, and records two numbers: `PSNR(original, watermarked)` for invisibility and `PSNR(original QR, recovered QR)` for recoverability. There is no attack here — this is the clean case, so it shows the baseline behaviour before Tasks 3 and 4 start damaging things.
4. Plots both curves side by side into `plots/task2_psnr_results.png`, one line per image.

The point is the shape of those curves. Raising alpha cannot help both goals at once. The left plot falls from about 43 dB at alpha = 0.01 to about 13 dB at alpha = 0.5 as the mark becomes visible, and in this clean setting the right plot falls too, because a larger alpha pushes more pixels past 1.0 where clipping destroys the information needed for recovery. Seeing both together is what lets me pick a sensible alpha instead of guessing, and it sets up Tasks 3 and 4, where adding a real attack makes the recovery curve develop an actual peak.
