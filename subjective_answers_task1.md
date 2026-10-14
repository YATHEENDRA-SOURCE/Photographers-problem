# Task 1 — Subjective Answers

**Roll No: 26210053**

---

### Q1. Why does using the top k singular values and vectors work? Can we use fewer? If yes, what is the minimum? If not, why?

A matrix of size H x W can have rank at most k = min(H, W). So every singular value after the k-th is already zero and adds nothing. That means the thin SVD with k components rebuilds the matrix exactly — it is not an approximation. When I tested my implementation against `np.linalg.svd`, the reconstruction error was about 4e-15, which is just floating point noise.

Keeping exactly k also makes the embedding work. The rule `sigma_i = sigma_i + alpha * sigma^q_i` pairs the cover and watermark values one by one, so both need spectra of the same length. Our covers are 321x481 (k = 321) and the QR is resized to 321x321, so they match.

Yes, we can use fewer than k. Truncating to the top t gives the best rank-t approximation, and since singular values decay fast for natural images, a small t already looks close to the original — for Image 1, just 2 components hold 95% of the energy. But truncation is lossy, and it costs us twice: the watermarked photo becomes a blurred rank-t version (bad for invisibility), and the recovered QR is also rank-t.

The minimum depends on what you are asking:

- For **exact** reconstruction, the minimum is rank(M). All three covers are full rank (321). My QR has a numerical rank of only 183, so its last 138 singular values are already zero and could be dropped for free.
- For the **task** to still work, it is much smaller. I truncated my QR to t components and re-tested decoding, and it still read `26210053` down to **t = 9**. The top 10 singular values already hold about 98% of the QR's energy, and QR codes have built-in error correction, so they survive a lot of blurring.

So top k is the safe choice, fewer is possible, and my practical floor was 9 components — though I would not truncate the cover in practice, since that damages the photo we are trying to protect.

---

### Q2. Cover image H x W, watermark l x l with l < min(H, W). Which singular values of the cover do you add the watermark's to, and why?

**Answer: (a) the top l singular values.**

**(c) is not possible.** The watermark only has l singular values but the cover has k > l. The embedding is a one-to-one index pairing, so there is nothing to add to the remaining k - l positions.

**(b) the least l is a bad idea.** The bottom of the spectrum is exactly what every real operation throws away — JPEG quantisation, denoising, resizing, even 8-bit rounding. If the watermark lived there, `(sigma'_i - sigma_i)` would be near zero after any attack, and then we divide by a small alpha, which blows up whatever noise is left. The mark would be invisible but useless.

**(a) the top l is right.** The leading singular values carry the dominant structure and most of the energy, and they are the most stable under distortion. Noise or compression perturbs them only slightly in relative terms, so the difference still recovers a usable `alpha * sigma^q_i`. Also, since sigma_1 is large, adding `alpha * sigma^q_1` is a small relative change, and we rebuild with the cover's own U and V^T so the photo keeps its appearance.

My Task 4 results support this: at alpha = 0.05 the QR still decoded after JPEG compression down to quality 30 for all three images, which only works because the mark sits where compression does not cut.

There is a trade-off — putting energy in the top singular values is more visible, and too large an alpha causes clipping. But robustness matters more for an ownership watermark, and alpha is the knob we use to manage visibility.
