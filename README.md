# Post-Quantum Authenticated Chaotic Image Encryption Framework

This repository contains a **research prototype implementation** of a hybrid cryptographic framework that integrates **post-quantum cryptography and chaos-based image encryption** for secure image transmission.

The system combines **NIST standardized post-quantum algorithms** with a **3-dimensional e-Log chaotic map** to provide confidentiality, authentication, and strong diffusion properties for digital images.

---

# Key Features

* Post-Quantum Key Exchange using **ML-KEM (FIPS 203)**
* Post-Quantum Digital Signatures using **ML-DSA (FIPS 204)**
* Context-bound key derivation using **HKDF-SHA3**
* Image-dependent chaotic parameter generation
* **3-D e-Log chaotic map** for confusion and diffusion
* Chaotic row and column permutation
* Chaotic rotation based scrambling
* XOR diffusion mask derived from chaotic sequences
* End-to-end authenticated encryption
* Replay-resistant session design

---

# System Architecture

The framework follows a modular cryptographic pipeline:

```
ML-KEM Key Exchange
        │
        ▼
Shared Secret
        │
        ▼
HKDF-SHA3 Key Derivation
        │
        ▼
Chaotic Parameter Generation
        │
        ▼
3-D e-Log Chaotic Image Encryption
        │
        ▼
Cipher Image
        │
        ▼
ML-DSA Authentication
```

---

# Encryption Workflow

## 1. Post-Quantum Key Establishment

A shared secret is established using **ML-KEM**.

```
(ek, dk) ← ML_KEM_KEYGEN()
(ss, ct) ← ML_KEM_ENCAPS(ek)
ss ← ML_KEM_DECAPS(dk, ct)
```

This produces a shared secret used for secure session key derivation.

---

## 2. Session Key Derivation

Session keys are derived using **HKDF-SHA3** with domain separation.

Inputs:

* Shared secret
* Sender ID
* Receiver ID
* Session ID
* Timestamp
* Image hash

Derived keys:

* `K_enc` – encryption key
* `K_mask` – masking key for image hash
* `K_chaos` – chaotic parameter seed

---

## 3. Chaotic Parameter Generation

A **320-bit derived key** is partitioned into six values:

```
u, v, w → control parameters
x0, y0, z0 → initial chaotic states
```

These parameters initialize the chaotic system.

---

## 4. 3-D e-Log Chaotic System

The encryption scheme uses a nonlinear chaotic map:

```
x_{i+1} = (x_i + u (e − ln(y_i))) mod 1
y_{i+1} = (y_i v + (e − ln(x_{i+1}))) mod 1
z_{i+1} = (z_i^{x_{i+1}} + w ln(y_{i+1})) mod 1
```

This map generates pseudo-random sequences used for permutation and diffusion.

---

## 5. Chaotic Image Encryption

The encryption pipeline consists of:

1. Chaotic mask generation
2. Row permutation
3. Column permutation
4. Row and column rotations
5. XOR diffusion

Final cipher image:

```
C = S XOR Mask
```

Where

* **S** = scrambled image
* **Mask** = chaotic diffusion mask

---

## 6. Authentication

To ensure integrity and authenticity, the cipher image is signed using **ML-DSA**.

```
H = SHA3-256(transcript || cipher_image)
signature = ML-DSA.sign(sk, H)
```

The receiver verifies the signature before decrypting the image.

---

# Decryption Process

The receiver performs:

1. Signature verification
2. ML-KEM decapsulation
3. Chaotic parameter reconstruction
4. Mask regeneration
5. Inverse rotations
6. Inverse permutations
7. XOR mask removal

Final integrity verification:

```
SHA3(recovered_image) == original_image_hash
```

---

# Requirements

Python **3.9+**

Install required packages:

```
pip install numpy pillow
```

---

# Running the Prototype

Place an image named:

```
splash.tiff
```

in the project directory and run:

```
python Module_eLog.py
```

Output files generated:

```
cipher_output.tiff
recovered_output.tiff
```

Optional intermediate debug images:

```
01_mask_image.tiff
02_after_row_permute.tiff
03_after_column_permute.tiff
04_after_row_rotate.tiff
05_after_column_rotate.tiff
```

---

# Project Structure

```
.
├── main.py
├── splash.tiff
├── cipher_output.tiff
├── recovered_output.tiff
└── README.md
```

---

# Security Notes

This implementation is a **research-oriented prototype** intended for:

* academic experimentation
* algorithm demonstration
* reproducibility of research results

It has **not undergone formal security auditing** and should **not be used in production systems**.

---

# Research Context

This work demonstrates a **post-quantum secure chaotic encryption framework** that integrates:

* lattice-based cryptography
* hash-based key derivation
* nonlinear chaotic dynamics

to achieve secure and quantum-resistant image transmission.

---

# License

This project is provided for **research and educational purposes**.
