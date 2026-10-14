# %%
# Imports
# ================================================================
# Don't update these imports. 
import os
import cv2
import glob
import getpass
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()
# %%
# Helper Functions
# ================================================================
# This are helper functions that you can use in your implementation.
# Don't update these functions

os.makedirs("plots", exist_ok=True)

def load_image_as_grayscale(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = image.astype(np.float32) / 255.0  # Normalize to [0, 1]
    return image

def load_image_as_rgb(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    image = image.astype(np.float32) / 255.0  # Normalize to [0, 1]
    return image

# ================================================================

# %%
# Task 1
# ======


def svd_decomposition(M: np.ndarray) -> tuple:
    """Perform SVD decomposition on an image
    
            Equivalent to np.linalg.svd(M, full_matrices=False), computed from the
            eigendecomposition of the smaller Gram matrix.
    
            Parameters
            ----------
            M : np.ndarray
                Input matrix of shape (H, W)
    
            Returns
            -------
            tuple
                U (H, k), sigma (k,), Vt (k, W) with k = min(H, W)
            """

    # Work in float64 throughout. The recovery step subtracts two sets of
    # singular values and divides by a small alpha, so float32 rounding noise
    # would show up directly in the recovered QR code.
    # Tolerance below which a singular value is treated as exactly zero.
    # (HINT 1: eigh can return tiny negative eigenvalues for a matrix that is
    # mathematically positive semi-definite.)
    SV_TOL = 1e-9

    M = np.asarray(M, dtype=np.float64)
    H, W = M.shape
    k = min(H, W)

    if H <= W:
        # M M^T is the (H, H) Gram matrix -> gives us U directly.
        G = M @ M.T
        eigvals, eigvecs = np.linalg.eigh(G)

        # eigh returns eigenvalues in ascending order; we want descending.
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        U = eigvecs[:, order]

        # HINT 1: clamp tiny negative eigenvalues to zero before the sqrt.
        eigvals = np.clip(eigvals, 0.0, None)
        sigma = np.sqrt(eigvals)
        sigma[sigma <= SV_TOL] = 0.0

        # Recover V^T from U instead of running a second eigendecomposition:
        #   M = U S V^T  =>  V^T = S^-1 U^T M   (for the non-zero sigmas)
        # Deriving one factor from the other is also what makes HINT 2 a
        # non-issue: whatever sign eigh picked for u_i, the matching v_i is
        # built from that same u_i, so M v_i = sigma_i u_i holds by
        # construction and no column can come out flipped.
        Vt = np.zeros((k, W), dtype=np.float64)
        nz = sigma > SV_TOL
        Vt[nz, :] = (U[:, nz].T @ M) / sigma[nz, None]
        U = U[:, :k]

    else:
        # H > W: the (W, W) Gram matrix M^T M is the smaller one -> gives V.
        G = M.T @ M
        eigvals, eigvecs = np.linalg.eigh(G)

        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        V = eigvecs[:, order]

        eigvals = np.clip(eigvals, 0.0, None)
        sigma = np.sqrt(eigvals)
        sigma[sigma <= SV_TOL] = 0.0

        # U = M V S^-1, again keeping the signs consistent by construction.
        U = np.zeros((H, k), dtype=np.float64)
        nz = sigma > SV_TOL
        U[:, nz] = (M @ V[:, nz]) / sigma[None, nz]
        Vt = V[:, :k].T

    return U, sigma, Vt

def add_watermark_single_channel(cover_image: np.ndarray, watermark: np.ndarray, alpha: float) -> np.ndarray:
    """Add watermark to a given channel of an image
    
        Parameters
        ----------
        cover_image : np.ndarray
            Image where watermark needs to be applied
        watermark : np.ndarray
            Watermark
        alpha : float
            Alpha to control the strength of watermark
    
        Returns
        -------
        np.ndarray
            Watermarked Image
        """

    # C = U S V^T  and  Q = Uq Sq Vq^T
    U, sigma, Vt = svd_decomposition(cover_image)
    _, sigma_q, _ = svd_decomposition(watermark)

    # Mix only the singular values: sigma~_i = sigma_i + alpha * sigma^q_i
    sigma_tilde = sigma + alpha * sigma_q

    # Rebuild with the cover's OWN U and V^T, so the photo still looks like
    # the photo -- only the "energy spectrum" has been nudged.
    watermarked_image = U @ np.diag(sigma_tilde) @ Vt

    # Clip so matplotlib can display it as-is.
    watermarked_image = np.clip(watermarked_image, 0.0, 1.0)
    return watermarked_image.astype(np.float32)


def recover_watermark(original_image: np.ndarray, watermarked_image: np.ndarray, watermark: np.ndarray, alpha: float) -> np.ndarray:
    """Recover watermark from a given channel of an image
    
        Parameters
        ----------
        original_image : np.ndarray
            Original image
        watermarked_image : np.ndarray
            Watermarked image
        watermark : np.ndarray
            Watermark
        alpha : float
            Alpha used during watermarking
    
        Returns
        -------
        np.ndarray
            Recovered watermark
        """

    # Part of the private key: the original photo's singular values.
    _, sigma, _ = svd_decomposition(original_image)

    # Decompose the (possibly damaged) copy we found on the internet.
    _, sigma_prime, _ = svd_decomposition(watermarked_image)

    # Rest of the key: the watermark's singular vectors.
    Uq, _, Vqt = svd_decomposition(watermark)

    # Undo the embedding: sigma~^q_i = (sigma'_i - sigma_i) / alpha
    sigma_q_tilde = (sigma_prime - sigma) / alpha

    recovered_watermark = Uq @ np.diag(sigma_q_tilde) @ Vqt
    recovered_watermark = np.clip(recovered_watermark, 0.0, 1.0)
    return recovered_watermark.astype(np.float32)


def add_watermark_rgb(cover_image: np.ndarray, watermark: np.ndarray, alpha: float) -> np.ndarray:
    """Add watermark to a given RGB image
        Parameters
        ----------
        cover_image : np.ndarray
            Image where watermark needs to be applied
        watermark : np.ndarray
            Watermark
        alpha : float
            Alpha to control the strength of watermark
    
        Returns
        -------
        np.ndarray
            Watermarked Image
        """

    # The single-channel routine already does the real work; each colour
    # channel is watermarked independently with the matching QR channel.
    watermarked_image = np.zeros_like(cover_image, dtype=np.float32)
    for c in range(cover_image.shape[2]):
        watermarked_image[:, :, c] = add_watermark_single_channel(
            cover_image[:, :, c], watermark[:, :, c], alpha
        )
    return watermarked_image

def recover_watermark_rgb(original_image: np.ndarray, watermarked_image: np.ndarray, watermark: np.ndarray, alpha: float) -> np.ndarray:
    """Recover watermark from a given RGB image
        Parameters
        ----------
        original_image : np.ndarray
            Original image
        watermarked_image : np.ndarray
            Watermarked image
        watermark : np.ndarray
            Watermark
        alpha : float
            Alpha used during watermarking
    
        Returns
        -------
        np.ndarray
            Recovered watermark
        """

    recovered_watermark = np.zeros_like(watermark, dtype=np.float32)
    for c in range(watermark.shape[2]):
        recovered_watermark[:, :, c] = recover_watermark(
            original_image[:, :, c], watermarked_image[:, :, c], watermark[:, :, c], alpha
        )
    return recovered_watermark


if __name__ == "__main__":

    image_paths = sorted(glob.glob("imgs/*.jpg"))
    images_rgb = [load_image_as_rgb(path) for path in image_paths]
    watermark_rgb = load_image_as_rgb(os.getenv("watermark_path"))
    # NOTE: All 3 provided cover images in imgs/ are (321, 481) i.e. same size,
    # so k = min(H, W) = 321 for every image. As described in questions.md, the
    # watermark is resized to (k, k) once here in a hard-coded manner rather than
    # dynamically per image.     
    watermark_rgb = cv2.resize(watermark_rgb, (321, 321))

    watermarked_images_rgb = []
    recovered_watermarks_rgb = []

    for image in images_rgb:
        # Apply watermarking to the image and recover the watermark from the watermarked image
        # ###############################################
        # Comment these lines and write your code here
        # alpha=0.05 keeps the watermarked photo at ~29-30 dB against the
        # original (visually near-identical) while the QR still scans cleanly.
        watermarked_image_rgb = add_watermark_rgb(image, watermark_rgb, alpha=0.05)
        recovered_rgb = recover_watermark_rgb(image, watermarked_image_rgb, watermark_rgb, alpha=0.05)
        # ###############################################

        watermarked_images_rgb.append(watermarked_image_rgb)
        recovered_watermarks_rgb.append(recovered_rgb)

    # 3x3 plots; first row: original images, second row: watermarked images, third row: recovered watermarks
    fig, axes = plt.subplots(3, 3, figsize=(12, 12))
    for i in range(3):
        axes[0, i].imshow(images_rgb[i])
        axes[0, i].set_title("Original Image")
        axes[0, i].axis("off")

        axes[1, i].imshow(watermarked_images_rgb[i])
        axes[1, i].set_title("Watermarked Image")
        axes[1, i].axis("off")

        axes[2, i].imshow(recovered_watermarks_rgb[i])
        axes[2, i].set_title("Recovered Watermark")
        axes[2, i].axis("off")
    plt.tight_layout()
    plt.savefig("plots/task1_results.png", metadata={"Author": getpass.getuser()})
