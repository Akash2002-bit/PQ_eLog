"""
=====================================================================
Post-Quantum Authenticated Chaotic Image Encryption Framework
Reference Prototype Implementation
=====================================================================

This Python program implements a research prototype of a hybrid
post-quantum cryptographic framework integrating:

    • ML-KEM (FIPS 203) — Post-Quantum Key Encapsulation
    • ML-DSA (FIPS 204) — Post-Quantum Digital Signatures
    • HKDF-SHA3        — Context-bound session key derivation
    • 3-D e-Log Chaos  — Image permutation and diffusion encryption

The system demonstrates a secure communication workflow for
image transmission that provides:

    ✔ Post-quantum confidentiality
    ✔ Post-quantum authentication
    ✔ session-bound key derivation
    ✔ image-dependent chaotic encryption
    ✔ replay resistance
    ✔ end-to-end integrity verification

This implementation is intended for **academic research,
experimentation, and algorithm validation**.

---------------------------------------------------------------------
Reference Research Model
---------------------------------------------------------------------

The implemented architecture corresponds to the modular
post-quantum chaotic encryption framework proposed in:

    "A Modular Post-Quantum Framework for Chaos-Based Image Encryption
     with an e-Log Map Instantiation"

Core idea:

    Post-Quantum Key Exchange
              │
              ▼
        Shared Secret (SS)
              │
              ▼
        HKDF-SHA3 Key Derivation
              │
              ▼
      Chaotic Parameter Generation
              │
              ▼
   3-D e-Log Image Confusion & Diffusion
              │
              ▼
        Authenticated Cipher Image

---------------------------------------------------------------------
Protocol Overview
---------------------------------------------------------------------

The protocol proceeds in the following stages.

1) Post-Quantum Key Establishment (ML-KEM)
------------------------------------------

The sender and receiver establish a shared secret using
Module-Lattice Key Encapsulation Mechanism (ML-KEM).

    (ek, dk) ← ML_KEM_KEYGEN()

    Sender:
        (ss, ct) ← ML_KEM_ENCAPS(ek)

    Receiver:
        ss ← ML_KEM_DECAPS(dk, ct)

This produces a 256-bit shared secret used for session key derivation.


2) Context-Bound Key Derivation
--------------------------------

Session-specific keys are derived using HKDF-SHA3 with
domain separation.

Inputs:

    ss      : shared secret
    pid_S   : sender identifier
    pid_R   : receiver identifier
    sid     : session ID
    ts      : timestamp
    P_img   : plaintext image bytes

Derived keys:

    K_enc   : encryption key
    K_mask  : masking key for image hash
    K_chaos : chaotic parameter key


Image-dependent initialization:

    h_img = SHA3-256(P_img)

    h_masked = h_img XOR K_mask

The masked hash is transmitted to enable deterministic
reconstruction of chaotic parameters by the receiver.


3) Chaotic Parameter Generation
--------------------------------

Chaotic parameters are derived from HKDF output.

    K_chaos = HKDF( PRK_chaos , "chaos" || context )

The 320-bit key is partitioned into six 53-bit values:

    u, v, w   → control parameters
    x0,y0,z0  → initial state

Each value is normalized to (0,1).


4) 3-D e-Log Chaotic System
---------------------------

The encryption algorithm uses the following discrete chaotic map:

    x_{i+1} = (x_i + u (e − ln(y_i))) mod 1
    y_{i+1} = (y_i v + (e − ln(x_{i+1}))) mod 1
    z_{i+1} = (z_i^{x_{i+1}} + w ln(y_{i+1})) mod 1

where:

    u, v, w ∈ (0,1)
    x_i, y_i, z_i ∈ (0,1)

The system provides:

    • strong sensitivity to initial conditions
    • nonlinear coupling across dimensions
    • large effective key space
    • high entropy chaotic sequences


5) Chaotic Image Encryption Pipeline
------------------------------------

Given an RGB image of size M × N:

STEP 1 — Mask Generation
    Chaotic sequence → pseudo-random mask

STEP 2 — Row Permutation
    Rows reordered using chaotic ordering

STEP 3 — Column Permutation
    Columns reordered using chaotic ordering

STEP 4 — Cyclic Rotations
    Rows and columns rotated using permutation indices

STEP 5 — Diffusion

    C = S XOR Mask

where

    S = scrambled image
    C = cipher image


6) Authentication (ML-DSA)
--------------------------

To ensure integrity and origin authentication:

    H = SHA3-256( transcript || cipher )

The sender signs H using ML-DSA.

    signature = ML-DSA.sign(sk_dsa, H)

Receiver verifies before decryption.

    verify(pk_dsa, H, signature)


7) Decryption Process
---------------------

Receiver performs:

    1. Signature verification
    2. ML-KEM decapsulation
    3. Chaotic parameter reconstruction
    4. Mask regeneration
    5. Inverse rotations
    6. Inverse permutations
    7. XOR mask removal

Final integrity check:

    SHA3(recovered_image) == original_image_hash


---------------------------------------------------------------------
Security Features
---------------------------------------------------------------------

This hybrid design provides:

    • Post-Quantum Confidentiality
    • Post-Quantum Authentication
    • Image-Dependent Encryption
    • Context-Bound Key Derivation
    • Replay Attack Resistance
    • Chaotic Confusion and Diffusion

The design achieves a large theoretical key space
(> 2^300 when chaotic parameters are included).


---------------------------------------------------------------------
Implementation Notes
---------------------------------------------------------------------

This code is a **research prototype**, not a production library.

Characteristics:

    • Python reference implementation
    • direct translation of algorithmic steps
    • emphasis on clarity rather than performance

Libraries used:

    numpy     — matrix operations
    pillow    — image processing
    hashlib   — SHA3 / SHAKE primitives
    secrets   — secure randomness


---------------------------------------------------------------------
Files Generated During Execution
---------------------------------------------------------------------

    cipher_output.tiff      — encrypted image
    recovered_output.tiff   — decrypted image

Optional debug snapshots:

    01_mask_image.tiff
    02_after_row_permute.tiff
    03_after_column_permute.tiff
    04_after_row_rotate.tiff
    05_after_column_rotate.tiff


---------------------------------------------------------------------
Disclaimer
---------------------------------------------------------------------

This software is intended for:

    • cryptographic research
    • reproducibility of academic results
    • algorithm demonstration

It has **not undergone formal security auditing** and must
not be used in production environments.

---------------------------------------------------------------------
"""


import hashlib
import math
import os
import sys
import hmac
import numpy as np
from PIL import Image
import time
import secrets

# =====================================================================
#                        ML-KEM (FIPS 203)
# =====================================================================

# Common parameters for ML-KEM
n = 256
q = 3329

# Global placeholders for ML-KEM 768
k = 2
eta1 = 2
eta2 = 2
du = 10
dv = 4


def generate_random_array():
    return [secrets.randbelow(256) for _ in range(32)]

def number_to_array(num):
    return [num]

def array_to_number(arr):
    if len(arr) == 1:
        return arr[0]
    else:
        raise ValueError("Array must contain exactly one element")

def BitsToBytes(b):
    B = [0] * (len(b) // 8)
    for i in range(len(b)):
        B[i // 8] += b[i] * (2 ** (i % 8))
    return B 

def BytesToBits(B):
    b = [0] * (8 * len(B))   
    C = B.copy() 
    for i in range(len(B)):
        for j in range(8):
            b[8 * i + j] = C[i] % 2 
            C[i] = math.floor(C[i]/2)
    return b

def reverse_bits_7bit(r):
    if r < 0 or r > 127:
        raise ValueError("Input must be a 7-bit integer (0 to 127).")
    binary_str = f'{r:07b}'
    reversed_binary_str = binary_str[::-1]
    return int(reversed_binary_str, 2)

def compress(ZQ, d):
    Z2D = [0]*(len(ZQ))
    for i in range(len(ZQ)):
        Z2D[i] = (round_nearest(((2**d) / q) * ZQ[i])) % (2**d)
    return Z2D

def decompress(Z2D, d):
    ZQ = [0] * len(Z2D)
    for i in range(len(Z2D)):
        ZQ[i] = round_nearest(((q/(2**d)) * Z2D[i]))
    return ZQ

def ByteEncode(F, d):
    b = [0] * (256 * d)
    for i in range(256):
        a = F[i] 
        for j in range(d):
            b[i * d + j] = a % 2
            a = (a - b[i * d + j]) // 2
    B = BitsToBytes(b)   
    return B

def ByteDecode(B, d):
    b = BytesToBits(B)
    F = [0] * 256
    m = 2**d if d < 12 else 3329
    for i in range(256):
        for j in range(d):
            F[i] += (b[i * d + j] * (2 ** j)%m)%m
        F[i] = F[i] % m    
    return F

def XOF_Init():
    return hashlib.shake_128()

def XOF_Absorb(ctx, B):
    return ctx.update(B) 

def XOF_Squeeze(ctx, length: int) -> bytes:
    return ctx.digest(8 * length)

def SampleNTT(B):   
    B = bytes(B[:])
    if len(B) != 34:
        raise ValueError("Input byte array must be exactly 34 bytes.")
    ctx = XOF_Init()   
    XOF_Absorb(ctx, B)  
    samples = [0] * 256  
    j = 0
    while j < 256:
        C = XOF_Squeeze(ctx, 3) 
        d1 = C[0] + 256 * (C[1] % 16)  
        d2 = (C[1] // 16) + 16 * C[2]  
        if d1 < q:
            samples[j] = d1
            j += 1
        if d2 < q and j < 256:
            samples[j] = d2
            j += 1
        if j < 256: 
            ctx.update(C) 
    return list(samples)

def SamplePolyCBD(B, eta):
    b = BytesToBits(B)
    f = [0]*256
    for i in range(256):
        x = sum(b[2*i*eta + j] for j in range(eta)) 
        y = sum(b[2*i*eta + eta + j] for j in range(eta)) 
        f[i] = (x - y) % q 
    return f

def NTT(f):
    n_len = len(f) 
    f_hat = f[:] 
    i = 1
    length = 128
    while length >= 2:
        for start in range(0, n_len, 2 * length):
            zeta = pow(17, reverse_bits_7bit(i)) % q
            i += 1
            for j in range(start, start + length):
                t = (zeta * f_hat[j + length]) % q
                f_hat[j + length] = (f_hat[j] - t) % q
                f_hat[j] = (f_hat[j] + t) % q
        length //= 2
    return f_hat

def NTTinverse(f_hat):
    f = f_hat[:] 
    n_len = len(f) 
    i = 127 
    length = 2
    while length <= 128:
        for start in range(0, n_len, 2 * length):
            zeta = pow(17, reverse_bits_7bit(i))%q 
            i -= 1  
            for j in range(start, start + length):
                t = f[j]
                f[j] = (t + f[j + length]) % q 
                f[j + length] = (zeta * (f[j + length] - t)) % q
        length *= 2 
    f = [(val * 3303) % q for val in f]   
    return f

def MultiplyNTTs(f_hat, g_hat):
    h_hat = [0] * 256
    for i in range(128):
        a0, a1 = f_hat[2 * i], f_hat[2 * i + 1]
        b0, b1 = g_hat[2 * i], g_hat[2 * i + 1]
        gamma = pow(17, 2*reverse_bits_7bit(i) + 1)
        h_hat[2 * i], h_hat[2 * i + 1] = BaseCaseMultiply(a0, a1, b0, b1, gamma)
    return h_hat

def BaseCaseMultiply(a0, a1, b0, b1, gamma):
    c0 = (a0 * b0 + a1 * b1 * gamma) % q
    c1 = (a0 * b1 + a1 * b0) % q
    return c0, c1 

def custom_add(list1, list2):
    result = [0] * 256
    for i in range(256):
        result[i] = (list1[i] + list2[i])%q 
    return result 

def custom_sub(list1, list2):
    result = [0] * 256
    for i in range(256):
        result[i] = (list1[i] - list2[i])%q 
    return result 

def add_nested_arrays(list1, list2):
    result = []
    for i in range(len(list1)):
        inner_result = [] 
        for j in range(len(list1[i])):
            inner_result.append((list1[i][j] + list2[i][j])%q)
        result.append(inner_result)   
    return result

def G_hash(x):
    input_bytes = bytes(x)
    sha3_hash = hashlib.sha3_512(input_bytes).digest()
    x1 = list(sha3_hash[:32])
    x2 = list(sha3_hash[32:])   
    return x1 + x2

def H_hash(x):
    input_bytes = bytes(x)
    sha3_hash = hashlib.sha3_256(input_bytes).digest()
    return list(sha3_hash[:32])

def J_hash(x):
    concatenated_input = bytes(x)
    output_length = 32
    shake = hashlib.shake_256()
    shake.update(concatenated_input)
    shake_output = shake.digest(output_length)
    return [int(byte) for byte in shake_output]

def PRF(array1, array2, eta):
    concatenated_input = bytes(array1) + bytes(array2)
    output_length = 64 * eta
    shake = hashlib.shake_256()
    shake.update(concatenated_input)
    shake_output = shake.digest(output_length)
    return [int(byte) for byte in shake_output]

def round_nearest(n_val):
    fractional_part = n_val - int(n_val)    
    if fractional_part == 0.5:
        return int(n_val) + 1  
    else:
        return round(n_val) 

def KeyGen(d):
    hash_val = G_hash(d+number_to_array(k))
    rho = hash_val[:32]
    sigma= hash_val[32:]
    N_counter = 0
    A_hat = [[[] for _ in range(k)] for _ in range(k)]
    for i in range(k):
        for j in range(k):
            A_hat[i][j] = SampleNTT((rho + number_to_array(j) + number_to_array(i)))
    s = [0]*k
    e = [0]*k
    for i in range(k):
        s[i] = (SamplePolyCBD(PRF(sigma, number_to_array(N_counter), eta1), eta1))
        N_counter += 1
    for i in range(k):
        e[i] = (SamplePolyCBD(PRF(sigma, number_to_array(N_counter), eta1), eta1))
        N_counter += 1
    s_hat = []
    e_hat = []       
    for i in range(k):
        s_hat.append(NTT(s[i]))
        e_hat.append(NTT(e[i]))
    t_hat = []
    Abar_sbar = []    
    for i in range(k):
        sum_arr = [0]*256    
        for j in range(k):
            product = MultiplyNTTs(A_hat[i][j],s_hat[j])
            sum_arr = custom_add(sum_arr, product)
        Abar_sbar.append(sum_arr)                                 
    t_hat = add_nested_arrays(Abar_sbar, e_hat)
    ekPKE_parts = []
    for i in range(k): 
        ekPKE_parts += (ByteEncode(t_hat[i], 12))
    ekPKE = ekPKE_parts[:] + rho
    dkPKE_parts = []
    for i in range(k): 
        dkPKE_parts += (ByteEncode(s_hat[i], 12))
    dkPKE = dkPKE_parts[:]
    return ekPKE, dkPKE

def Encrypt(ek_pke, m, r):   
    N_counter = 0
    t_hatparts = []
    for j in range(k):
        inner_list = ek_pke[384*j:384*(j+1)]
        t_hatparts.append(ByteDecode(inner_list, 12))        
    t_hat = t_hatparts[:]
    rho = ek_pke[384*k:384*k+32]
    A_hat = [[[] for _ in range(k)] for _ in range(k)]
    for i in range(k):
        for j in range(k):
            A_hat[i][j] = SampleNTT((rho + number_to_array(j) + number_to_array(i)))
    y = [0]*k
    e1 = [0]*k
    for i in range(k):
        y[i] = SamplePolyCBD(PRF(r, number_to_array(N_counter), eta1), eta1)
        N_counter +=1
    for i in range(k):
        e1[i] = SamplePolyCBD(PRF(r, number_to_array(N_counter), eta2), eta2)
        N_counter +=1                
    e2 = SamplePolyCBD(PRF(r, number_to_array(N_counter), eta2), eta2)
    y_hat = []
    for i in range(k):
        y_hat.append(NTT(y[i]))
    A_hatT = A_hat[:]
    At_y = []
    for i in range(k):
        sum1 = [0]*256    
        for j in range(k):
            product = NTTinverse(MultiplyNTTs(A_hatT[j][i],y_hat[j]))
            sum1 = custom_add(sum1, product)
        At_y.append(sum1)
    u = add_nested_arrays(At_y, e1)
    myu = decompress(ByteDecode(m, 1), 1)
    tT_y = []
    t_hatT = t_hat[:]
    sum2 = [0]*256  
    for j in range(k):
        product = (MultiplyNTTs(t_hatT[j], y_hat[j]))
        sum2 = custom_add(sum2, product)
    tT_y = sum2[:] 
    v = custom_add(custom_add(NTTinverse(tT_y), e2), myu)
    c1 = []
    for i in range(k):
        c1 += (ByteEncode(compress(u[i], du), du))       
    c2 = ByteEncode(compress(v, dv), dv)
    c = c1 + c2
    return c

def Decrypt(dk_pke, c):
    c1 = c[:32*du*k]
    c2 = c[32*du*k : 32*(du*k+dv)]
    c1_12 = []
    for i in range(k):
        start_index = i * 32 * du
        end_index = start_index + 32 * du
        inner_list = c[start_index:end_index]
        c1_12.append(inner_list) 
    u_bar = []
    for i in range(k):
        u_bar.append(decompress(ByteDecode(c1_12[i], du), du))
    v_bar = decompress(ByteDecode(c2, dv), dv)
    s_hat = []
    for i in range(k):
        start_index = i * 384
        end_index = start_index + 384
        inner_list = dk_pke[start_index:end_index]
        s_hat.append(ByteDecode(inner_list, 12)) 
    u_bar_hat = []
    for i in range(k):
        u_bar_hat.append(NTT(u_bar[i])) 
    st_ubarhat = [0]*256   
    for j in range(k):
        product = (MultiplyNTTs(s_hat[j], u_bar_hat[j]))
        st_ubarhat = custom_add(st_ubarhat, product)
    w  = custom_sub(v_bar, NTTinverse(st_ubarhat)) 
    m = ByteEncode(compress(w, 1), 1)
    return m

def KeyGen_internal(d, z):
    ek_pke, dk_pke = KeyGen(d)
    ek = ek_pke[:]
    dk = (dk_pke + ek + H_hash(ek) + z)
    return ek, dk
    
def Encaps_internal(ek, m):   
    hashkc = G_hash(m + H_hash(ek))
    K_val = hashkc[:32]
    r = hashkc[32:]   
    c = Encrypt(ek, m, r)
    return K_val, c

def Decaps_internal(dk, c):
    dk_pke = dk[:384*k]
    ek_pke = dk[384*k : 768*k + 32]
    h = dk[768*k + 32 : 768*k + 64]
    z = dk[768*k + 64 : 768*k + 96]
    m_bar = Decrypt(dk_pke, c)
    hashG_krbar = G_hash(m_bar + h)
    K_bar = hashG_krbar[:32]
    r_bar = hashG_krbar[32:]
    KKBAR = J_hash(z + c)
    c_bar = Encrypt(ek_pke, m_bar, r_bar)
    if(c != c_bar):
        K_bar = KKBAR
    return K_bar

def ML_KEM_KEYGEN():
    d = generate_random_array()
    z = generate_random_array()
    if(d==[] or z==[]):
        print("ERROR: KEYGEN Failed! (Random Bit Generation)")
        return None, None
    ek, dk = KeyGen_internal(d, z)
    return ek, dk
    
def ML_KEM_ENCAPS(ek):
    m = generate_random_array()
    if (m==[]):
        print("ERROR: ENCAPS Failed! (Random Bit Generation)")
        return None, None
    K_val, c = Encaps_internal(ek, m)
    return K_val, c
        
def ML_KEM_DECAPS(dk, c):
    K_bar = Decaps_internal(dk, c)
    return K_bar  


# =====================================================================
#                        ML-DSA (FIPS 204)
# =====================================================================

Q = 8380417
N = 256
D = 13
ROU = 1753 

ML_DSA_PARAMS = {
    "44": {
        "k": 4, "l": 4, "eta": 2, "tau": 39, "beta": 78,
        "gamma1": 2**17, "gamma2": (Q - 1) // 88, "omega": 80,
        "lambda": 128, "pk_size": 1312, "sk_size": 2560, "sig_size": 2420
    },
    "65": {
        "k": 6, "l": 5, "eta": 4, "tau": 49, "beta": 196,
        "gamma1": 2**19, "gamma2": (Q - 1) // 32, "omega": 55,
        "lambda": 192, "pk_size": 1952, "sk_size": 4032, "sig_size": 3309
    },
    "87": {
        "k": 8, "l": 7, "eta": 2, "tau": 60, "beta": 120,
        "gamma1": 2**19, "gamma2": (Q - 1) // 32, "omega": 75,
        "lambda": 256, "pk_size": 2592, "sk_size": 4896, "sig_size": 4627
    }
}

def get_zetas():
    roots = [pow(ROU, i, Q) for i in range(256)]
    br_roots = [0] * 256
    for i in range(256):
        rev = int('{:08b}'.format(i)[::-1], 2)
        br_roots[rev] = roots[i]
    return br_roots

ZETAS = get_zetas()

def ntt(poly):
    a = list(poly)
    k_idx = 1
    for m in [128, 64, 32, 16, 8, 4, 2, 1]:
        for i in range(0, 256, 2 * m):
            z = ZETAS[k_idx]
            k_idx += 1
            for j in range(i, i + m):
                t = (z * a[j + m]) % Q
                a[j + m] = (a[j] - t) % Q
                a[j] = (a[j] + t) % Q
    return a

def intt(poly):
    a = list(poly)
    k_idx = 255
    for m in [1, 2, 4, 8, 16, 32, 64, 128]:
        for i in range(0, 256, 2 * m):
            for j in range(i, i + m):
                z = ZETAS[k_idx]
                t = a[j]
                a[j] = (t + a[j + m]) % Q
                a[j + m] = (z * (a[j + m] - t)) % Q
            k_idx -= 1
    inv_n = pow(N, Q - 2, Q)
    return [(x * inv_n) % Q for x in a]

def poly_add(a, b): return [(x + y) % Q for x, y in zip(a, b)]
def poly_sub(a, b): return [(x - y) % Q for x, y in zip(a, b)]
def poly_mul_pointwise(a, b): return [(x * y) % Q for x, y in zip(a, b)]
def to_signed(poly): return [x if x <= Q//2 else x - Q for x in poly]

def power2round(r):
    r_plus = r % Q
    r0 = (r_plus % (1 << D))
    if r0 > (1 << (D - 1)): r0 -= (1 << D)
    return (r_plus - r0) >> D, r0

def decompose(r, gamma2):
    r_plus = r % Q
    r0 = r_plus % (2 * gamma2)
    if r0 > gamma2: r0 -= 2 * gamma2
    if r_plus - r0 == Q - 1:
        return 0, r0 - 1
    return (r_plus - r0) // (2 * gamma2), r0

def high_bits(r, gamma2): return decompose(r, gamma2)[0] 
def low_bits(r, gamma2): return decompose(r, gamma2)[1]  

def make_hint(z, r, gamma2):
    r1 = high_bits(r, gamma2)
    v1 = high_bits(r + z, gamma2)
    return 1 if r1 != v1 else 0

def use_hint(h, r, gamma2):
    m = (Q - 1) // (2 * gamma2)
    r1, r0 = decompose(r, gamma2)
    if h == 1:
        if r0 > 0: return (r1 + 1) % m
        else: return (r1 - 1) % m
    return r1

def simple_bit_pack(w, bitlen):
    z = bytearray()
    curr_val = 0
    curr_bits = 0
    for coeff in w:
        curr_val |= (coeff << curr_bits)
        curr_bits += bitlen
        while curr_bits >= 8:
            z.append(curr_val & 0xFF)
            curr_val >>= 8
            curr_bits -= 8
    if curr_bits > 0:
        z.append(curr_val & 0xFF)
    return bytes(z)

def simple_bit_unpack(v, bitlen, num_coeffs=256):
    w = []
    curr_val = 0
    curr_bits = 0
    idx = 0
    mask = (1 << bitlen) - 1
    for _ in range(num_coeffs):
        while curr_bits < bitlen and idx < len(v):
            curr_val |= (v[idx] << curr_bits)
            curr_bits += 8
            idx += 1
        w.append(curr_val & mask)
        curr_val >>= bitlen
        curr_bits -= bitlen
    return w

def bit_pack(w, a, b, bitlen):
    shifted = [b - val for val in w]
    return simple_bit_pack(shifted, bitlen)

def bit_unpack(v, a, b, bitlen):
    shifted = simple_bit_unpack(v, bitlen)
    return [b - val for val in shifted]

def hint_bit_pack(h_vec, omega, k_param):
    y = bytearray([0] * (omega + k_param))
    index = 0
    for i in range(k_param):
        for j in range(N):
            if h_vec[i][j] != 0:
                y[index] = j
                index += 1
        y[omega + i] = index
    return bytes(y)

def hint_bit_unpack(y, omega, k_param):
    h = [[0]*N for _ in range(k_param)]
    index = 0
    for i in range(k_param):
        limit = y[omega + i]
        if limit < index or limit > omega: return None
        last = -1
        while index < limit:
            pos = y[index]
            if pos <= last: return None
            last = pos
            h[i][pos] = 1
            index += 1
    for i in range(index, omega):
        if y[i] != 0: return None
    return h

def shake128(data, length): return hashlib.shake_128(data).digest(length)
def shake256(data, length): return hashlib.shake_256(data).digest(length)

def rej_ntt_poly(seed):
    out = []
    ctx = hashlib.shake_128(seed)
    block = ctx.digest(840)
    ptr = 0
    while len(out) < N:
        if ptr + 3 > len(block): block += ctx.digest(168)
        val = (block[ptr] | (block[ptr+1] << 8) | (block[ptr+2] << 16)) & 0x7FFFFF
        ptr += 3
        if val < Q: out.append(val)
    return out

def rej_bounded_poly(seed, eta):
    out = []
    ctx = hashlib.shake_256(seed)
    block = ctx.digest(512)
    ptr = 0
    while len(out) < N:
        if ptr >= len(block): block += ctx.digest(128)
        z = block[ptr]
        z0, z1 = z & 0x0F, z >> 4
        ptr += 1
        if eta == 2:
            if z0 < 5: out.append(2 - z0)
            if len(out) < N and z1 < 5: out.append(2 - z1)
        elif eta == 4:
            if z0 < 9: out.append(4 - z0)
            if len(out) < N and z1 < 9: out.append(4 - z1)
    return out

def expand_a(rho, k_param, l_param):
    matrix = [[None for _ in range(l_param)] for _ in range(k_param)]
    for r in range(k_param):
        for s in range(l_param):
            matrix[r][s] = rej_ntt_poly(rho + bytes([s, r]))
    return matrix

def expand_s(rho, k_param, l_param, eta):
    s1 = [rej_bounded_poly(rho + bytes([i, 0]), eta) for i in range(l_param)]
    s2 = [rej_bounded_poly(rho + bytes([i + l_param, 0]), eta) for i in range(k_param)]
    return s1, s2

def expand_mask(rho, mu, l_param, gamma1):
    y = []
    bitlen = 18 if gamma1 == 2**17 else 20
    for r in range(l_param):
        seed = rho + (mu + r).to_bytes(2, 'little')
        req_bytes = (256 * bitlen + 7) // 8
        raw = shake256(seed, req_bytes)
        y.append([gamma1 - val for val in simple_bit_unpack(raw, bitlen)])
    return y

def sample_in_ball(seed, tau):
    h_out = shake256(seed, 8 + 128)
    signs = int.from_bytes(h_out[:8], 'little')
    c = [0] * N
    rng = h_out[8:]
    rng_idx = 0
    for i in range(N - tau, N):
        while True:
            if rng_idx >= len(rng): rng += shake256(seed, 128)
            j = rng[rng_idx]
            rng_idx += 1
            if j <= i: break
        c[i] = c[j]
        s_bit = (signs >> (i - (N - tau))) & 1
        c[j] = -1 if s_bit else 1
    return c

def pk_encode(rho, t1):
    pk = rho
    for poly in t1: pk += simple_bit_pack(poly, 10)
    return pk

def pk_decode(pk, k_param):
    rho = pk[:32]
    t1_bytes = pk[32:]
    t1 = []
    chunk_size = (N * 10) // 8
    for i in range(k_param):
        chunk = t1_bytes[i*chunk_size : (i+1)*chunk_size]
        t1.append(simple_bit_unpack(chunk, 10))
    return rho, t1

def sk_encode(rho, K, tr, s1, s2, t0, eta, d):
    sk = rho + K + tr
    s_bitlen = 3 if eta == 2 else 4
    for poly in s1: sk += bit_pack(poly, -eta, eta, s_bitlen)
    for poly in s2: sk += bit_pack(poly, -eta, eta, s_bitlen)
    for poly in t0: sk += bit_pack(poly, - (1<<(d-1)) + 1, (1<<(d-1)), d)
    return sk

def sk_decode(sk, k_param, l_param, eta, d):
    ptr = 0
    rho = sk[ptr:ptr+32]; ptr += 32
    K = sk[ptr:ptr+32]; ptr += 32
    tr = sk[ptr:ptr+64]; ptr += 64
    s_bitlen = 3 if eta == 2 else 4
    s1_bytes = (N * s_bitlen) // 8
    s1, s2, t0 = [], [], []
    for _ in range(l_param):
        s1.append(bit_unpack(sk[ptr:ptr+s1_bytes], -eta, eta, s_bitlen)); ptr += s1_bytes
    for _ in range(k_param):
        s2.append(bit_unpack(sk[ptr:ptr+s1_bytes], -eta, eta, s_bitlen)); ptr += s1_bytes
    t0_bytes = (N * d) // 8
    for _ in range(k_param):
        t0.append(bit_unpack(sk[ptr:ptr+t0_bytes], - (1<<(d-1)) + 1, (1<<(d-1)), d)); ptr += t0_bytes
    return rho, K, tr, s1, s2, t0

def sig_encode(c_tilde, z, h, gamma1, omega, k_param):
    sig = c_tilde
    z_bitlen = 18 if gamma1 == 2**17 else 20
    z_signed = [to_signed(p) for p in z]
    for poly in z_signed:
        sig += bit_pack(poly, -gamma1 + 1, gamma1, z_bitlen)
    sig += hint_bit_pack(h, omega, k_param)
    return sig

def sig_decode(sig, k_param, l_param, gamma1, omega, lambda_bits):
    c_len = lambda_bits // 4
    c_tilde = sig[:c_len]
    ptr = c_len
    z_bitlen = 18 if gamma1 == 2**17 else 20
    z_bytes = (N * z_bitlen) // 8
    z = []
    for _ in range(l_param):
        z.append(bit_unpack(sig[ptr:ptr+z_bytes], -gamma1 + 1, gamma1, z_bitlen))
        ptr += z_bytes
    h = hint_bit_unpack(sig[ptr:], omega, k_param)
    return c_tilde, z, h

def w1_encode(w1, gamma2):
    bitlen = 6 if gamma2 == (Q-1)//88 else 4
    out = bytearray()
    for poly in w1: out += simple_bit_pack(poly, bitlen)
    return bytes(out)

class MLDSA:
    def __init__(self, mode):
        if mode not in ML_DSA_PARAMS: raise ValueError("Invalid mode")
        self.params = ML_DSA_PARAMS[mode]
        self.k, self.l = self.params['k'], self.params['l']
        self.eta, self.tau = self.params['eta'], self.params['tau']
        self.beta, self.omega = self.params['beta'], self.params['omega']
        self.gamma1, self.gamma2 = self.params['gamma1'], self.params['gamma2']
        self.c_len = self.params['lambda'] // 4

    def keygen(self):
        zeta = os.urandom(32)
        seed_blob = shake256(zeta + bytes([self.k, self.l]), 128)
        rho, rho_prime, K = seed_blob[:32], seed_blob[32:96], seed_blob[96:128]
        A_ntt = expand_a(rho, self.k, self.l)
        s1, s2 = expand_s(rho_prime, self.k, self.l, self.eta)
        s1_ntt = [ntt(p) for p in s1]
        t = []
        for r in range(self.k):
            row_accum = [0] * N
            for c in range(self.l):
                prod = poly_mul_pointwise(A_ntt[r][c], s1_ntt[c])
                row_accum = poly_add(row_accum, prod)
            t.append(poly_add(intt(row_accum), s2[r]))
        t1, t0 = [], []
        for poly in t:
            p1, p0 = [], []
            for coef in poly:
                x, y = power2round(coef)
                p1.append(x); p0.append(y)
            t1.append(p1); t0.append(p0)
        pk = pk_encode(rho, t1)
        tr = shake256(pk, 64)
        sk = sk_encode(rho, K, tr, s1, s2, t0, self.eta, D)
        return pk, sk

    def sign(self, sk, message, ctx=b""):
        if len(ctx) > 255: raise ValueError("Context too long")
        m_prime = bytes([0, len(ctx)]) + ctx + message
        rho, K, tr, s1, s2, t0 = sk_decode(sk, self.k, self.l, self.eta, D)
        mu = shake256(tr + m_prime, 64)
        rnd = os.urandom(32)
        rho_dp = shake256(K + rnd + mu, 64)
        s1_ntt, s2_ntt, t0_ntt = [ntt(p) for p in s1], [ntt(p) for p in s2], [ntt(p) for p in t0]
        A_ntt = expand_a(rho, self.k, self.l)
        kappa, attempts = 0, 0
        
        while True:
            attempts += 1
            if attempts % 200 == 0: print(f"  [Attempt {attempts}]")
            y = expand_mask(rho_dp, kappa, self.l, self.gamma1)
            kappa += self.l
            y_ntt = [ntt(p) for p in y]
            w = []
            for r in range(self.k):
                acc = [0] * N
                for c in range(self.l):
                    acc = poly_add(acc, poly_mul_pointwise(A_ntt[r][c], y_ntt[c]))
                w.append(intt(acc))
            w1 = [[high_bits(c, self.gamma2) for c in p] for p in w]
            c_tilde = shake256(mu + w1_encode(w1, self.gamma2), self.c_len)
            c_poly = sample_in_ball(c_tilde, self.tau)
            c_ntt = ntt(c_poly)
            z = []
            for i in range(self.l):
                cs1 = intt(poly_mul_pointwise(c_ntt, s1_ntt[i]))
                z.append(poly_add(y[i], cs1))
            limit_z = self.gamma1 - self.beta
            if any(any(abs(x if x<=Q//2 else x-Q) >= limit_z for x in p) for p in z): continue
            
            r0 = []
            for i in range(self.k):
                cs2 = intt(poly_mul_pointwise(c_ntt, s2_ntt[i]))
                r0.append([low_bits(coef, self.gamma2) for coef in poly_sub(w[i], cs2)])
            limit_r0 = self.gamma2 - self.beta
            if any(any(abs(x if x<=Q//2 else x-Q) >= limit_r0 for x in p) for p in r0): continue

            ct0 = [intt(poly_mul_pointwise(c_ntt, p)) for p in t0_ntt]
            if any(any(abs(x if x<=Q//2 else x-Q) >= self.gamma2 for x in p) for p in ct0): continue

            h, ones = [], 0
            for i in range(self.k):
                cs2 = intt(poly_mul_pointwise(c_ntt, s2_ntt[i]))
                w_approx = poly_add(poly_sub(w[i], cs2), ct0[i])
                hi = [make_hint(-ct0[i][j], w_approx[j], self.gamma2) for j in range(N)]
                h.append(hi); ones += sum(hi)
            if ones > self.omega: continue
            return sig_encode(c_tilde, z, h, self.gamma1, self.omega, self.k)

    def verify(self, pk, message, sig, ctx=b""):
        if len(ctx) > 255: return False
        m_prime = bytes([0, len(ctx)]) + ctx + message
        rho, t1 = pk_decode(pk, self.k)
        c_tilde, z, h = sig_decode(sig, self.k, self.l, self.gamma1, self.omega, self.params['lambda'])
        if h is None: return False
        A_ntt = expand_a(rho, self.k, self.l)
        tr = shake256(pk, 64)
        mu = shake256(tr + m_prime, 64)
        c_poly = sample_in_ball(c_tilde, self.tau)
        c_ntt = ntt(c_poly)
        z_ntt = [ntt(p) for p in z]
        w_prime, w1_prime = [], []
        for r in range(self.k):
            acc = [0] * N
            for c in range(self.l):
                acc = poly_add(acc, poly_mul_pointwise(A_ntt[r][c], z_ntt[c]))
            Az = intt(acc)
            ct1 = intt(poly_mul_pointwise(c_ntt, ntt([(c << D) % Q for c in t1[r]])))
            w_prime.append(poly_sub(Az, ct1))
            w1_prime.append([use_hint(h[r][j], w_prime[r][j], self.gamma2) for j in range(N)])
        
        c_tilde_prime = shake256(mu + w1_encode(w1_prime, self.gamma2), self.c_len)
        limit_z = self.gamma1 - self.beta
        if any(any(abs(x) >= limit_z for x in p) for p in z): return False
        return c_tilde == c_tilde_prime



# =====================================================================
#           HKDF-SHA3 
# =====================================================================


def hkdf_extract_sha3(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt, ikm, hashlib.sha3_256).digest()

def hkdf_expand_sha3(prk: bytes, info: bytes, length: int) -> bytes:
    okm = b""
    t = b""
    counter = 1

    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha3_256).digest()
        okm += t
        counter += 1

    return okm[:length]


def sender_key_derivation(ss, ct, P_img, pid_S, pid_R, sid, ts):

    info_enc  = b"enc"  + pid_S + pid_R + sid + ts
    info_mask = b"mask" + pid_S + pid_R + sid + ts

    K_enc  = hkdf_expand_sha3(ss, info_enc, 32)
    K_mask = hkdf_expand_sha3(ss, info_mask, 32)

    h_img = hashlib.sha3_256(P_img).digest()

    h_masked = bytes(a ^ b for a, b in zip(h_img, K_mask))

    PRK_chaos = hkdf_extract_sha3(h_img, K_enc)

    info_chaos = b"chaos" + pid_S + pid_R + sid + ts
    K_chaos = hkdf_expand_sha3(PRK_chaos, info_chaos, 40)   # 320 bits

    K = int.from_bytes(K_chaos, 'big')

    mask = (1 << 53) - 1

    u  = ((K >> (53*5)) & mask) / 2**53
    v  = ((K >> (53*4)) & mask) / 2**53
    w  = ((K >> (53*3)) & mask) / 2**53
    x0 = ((K >> (53*2)) & mask) / 2**53
    y0 = ((K >> (53*1)) & mask) / 2**53
    z0 = ((K >> (53*0)) & mask) / 2**53  
    return K_enc, K_mask, h_masked, u, v, w, x0, y0, z0

def receiver_key_derivation(ss, ct, h_masked, pid_S, pid_R, sid, ts):

    info_enc  = b"enc"  + pid_S + pid_R + sid + ts
    info_mask = b"mask" + pid_S + pid_R + sid + ts

    K_enc  = hkdf_expand_sha3(ss, info_enc, 32)
    K_mask = hkdf_expand_sha3(ss, info_mask, 32)

    h_img = bytes(a ^ b for a, b in zip(h_masked, K_mask))

    PRK_chaos = hkdf_extract_sha3(h_img, K_enc)

    info_chaos = b"chaos" + pid_S + pid_R + sid + ts
    K_chaos = hkdf_expand_sha3(PRK_chaos, info_chaos, 40)   # 320 bits

    K = int.from_bytes(K_chaos, 'big')

    mask = (1 << 53) - 1

    u  = ((K >> (53*5)) & mask) / 2**53
    v  = ((K >> (53*4)) & mask) / 2**53
    w  = ((K >> (53*3)) & mask) / 2**53
    x0 = ((K >> (53*2)) & mask) / 2**53
    y0 = ((K >> (53*1)) & mask) / 2**53
    z0 = ((K >> (53*0)) & mask) / 2**53  
    return K_enc, K_mask, h_img, u, v, w, x0, y0, z0


E_CONST = 2.71828182845904524


# ==========================================================
# 3-D e-log chaotic system
# ==========================================================

def chaotic_step(x,y,z,u,v,w):

    x = (x + u*(E_CONST - math.log(y))) % 1
    y = (y*v + (E_CONST - math.log(x))) % 1
    z = (pow(z, x) + w*math.log(y)) % 1

    return x,y,z

# Helper to save intermediate steps
def save_step(img_array, filename):
    Image.fromarray(img_array.astype(np.uint8)).save(f"{filename}.tiff")
    print(f"Captured: {filename}.tiff")

# ==========================================================
# Algorithm 1: Mask Generation
# ==========================================================
def generate_mask(M, N, u, v, w, x, y, z, save_img=False):
    L = M * N
    xs, ys, zs = [], [], []
    for _ in range(L):
        x, y, z = chaotic_step(x, y, z, u, v, w)
        xs.append(x); ys.append(y); zs.append(z)
        
    S = xs + ys + zs
    Z = np.floor(np.mod(np.array(S)*1e15, 256)).astype(np.uint8)
    mask = Z.reshape((M, N, 3))
    
    if save_img:
        save_step(mask, "01_mask_image")
        
    return mask, x, y, z

# ==========================================================
# Algorithm 2: Row and Column Permutation
# ==========================================================
def chaotic_permutation(img, u, v, w, x, y, z, save_img=False):
    M, N, _ = img.shape
    
    # Row sequence
    row_seq = []
    for _ in range(M):
        x, y, z = chaotic_step(x, y, z, u, v, w)
        row_seq.append((x + y + z) % 1)
    rowscm = np.argsort(row_seq)
    
    I_r = img[rowscm, :, :]
    if save_img:
        save_step(I_r, "02_after_row_permute")

    # Col sequence
    col_seq = []
    for _ in range(N):
        x, y, z = chaotic_step(x, y, z, u, v, w)
        col_seq.append((x + y + z) % 1)
    colscm = np.argsort(col_seq)

    I_p = I_r[:, colscm, :]
    if save_img:
        save_step(I_p, "03_after_column_permute")
        
    return I_p, x, y, z, rowscm, colscm

# ==========================================================
# Algorithm 3: Row and Column Rotations
# ==========================================================
def chaotic_rotation(I_p, rowscm, colscm, save_img=False):
    M, N, _ = I_p.shape
    S = I_p.copy()

    # Row Rotate
    for i in range(M):
        shift = rowscm[i] % N
        S[i] = np.roll(S[i], shift, axis=0)
    if save_img:
        save_step(S, "04_after_row_rotate")

    # Col Rotate
    for j in range(N):
        shift = colscm[j] % M
        S[:, j] = np.roll(S[:, j], shift, axis=0)
    if save_img:
        save_step(S, "05_after_column_rotate")

    return S

# ==========================================================
# Full Encryption
# ==========================================================
def chaotic_encrypt(img, u, v, w, x0, y0, z0):
    M, N, _ = img.shape
    
    # We pass save_img=True only during encryption
    mask, x, y, z = generate_mask(M, N, u, v, w, x0, y0, z0, save_img=True)
    I_p, x, y, z, rowscm, colscm = chaotic_permutation(img, u, v, w, x, y, z, save_img=True)
    S = chaotic_rotation(I_p, rowscm, colscm, save_img=True)
    
    C = np.bitwise_xor(S, mask)
    
    return C, rowscm, colscm

# ==========================================================
# Full Decryption (Restored to normal, no intermediate saves)
# ==========================================================
def chaotic_decrypt(cipher, u, v, w, x0, y0, z0):
    M, N, _ = cipher.shape
    
    # Passing save_img=False prevents overwriting our saved files
    mask, x, y, z = generate_mask(M, N, u, v, w, x0, y0, z0, save_img=False)
    _, x, y, z, rowscm, colscm = chaotic_permutation(cipher, u, v, w, x, y, z, save_img=False)

    S = np.bitwise_xor(cipher, mask)

    for j in range(N):
        shift = colscm[j] % M
        S[:, j] = np.roll(S[:, j], -shift, axis=0)

    for i in range(M):
        shift = rowscm[i] % N
        S[i] = np.roll(S[i], -shift, axis=0)

    inv_cols = np.argsort(colscm)
    S = S[:, inv_cols, :]

    inv_rows = np.argsort(rowscm)
    I = S[inv_rows, :, :]

    return I
# =====================================================================
#                        COMBINED EXECUTION
# =====================================================================

if __name__ == "__main__":

    print("=====================================================")
    print(" Post-Quantum Cryptography Suite (FIPS 203 & 204 + Chaos)")
    print("=====================================================")

    # ---------------- ML-KEM TEST ----------------
    print("\n--- ML-KEM ---")
    k, eta1, eta2, du, dv = 3, 2, 2, 10, 4  # ML-KEM-768
    ek, dk = ML_KEM_KEYGEN()
    ss, ct = ML_KEM_ENCAPS(ek)
    ss_dec = ML_KEM_DECAPS(dk, ct)

    print("Shared Secret Match:", ss == ss_dec)

    # ---------------- ML-DSA TEST ----------------
    print("\n--- ML-DSA ---")
    mldsa = MLDSA("65")
    pk_dsa, sk_dsa = mldsa.keygen()

    message = b"Post-Quantum Authenticated Encryption"
    signature = mldsa.sign(sk_dsa, message)

    print("Signature Valid:",
          mldsa.verify(pk_dsa, message, signature))


    # ---------------- PQ CHAOTIC IMAGE PROTOCOL ----------------
    print("\n--- PQ Chaotic Image Encryption ---")

    image_path = "splash.tiff"
    if not os.path.exists(image_path):
        print("Place splash.tiff in the same folder.")
        sys.exit()

    img = np.array(Image.open(image_path).convert("RGB"))
    P_img_bytes = img.tobytes()

    # ----------- Session Context -----------
    pid_S = b"Sender_A"
    pid_R = b"Receiver_B"
    sid   = os.urandom(16)  # 128-bit session ID
    ts    = int(time.time()).to_bytes(8, 'big')

    # ----------- Sender Side Derivation -----------
    K_enc, K_mask, h_masked, u, v, w, x0, y0, z0 = sender_key_derivation(
        bytes(ss),
        bytes(ct),
        P_img_bytes,
        pid_S,
        pid_R,
        sid,
        ts
    )
    cipher_img, rowscm, colscm = chaotic_encrypt(img.copy(), u, v, w, x0, y0, z0)
    # ----------- Build Authentication Transcript -----------
    info_auth = pid_S + pid_R + sid + ts + bytes(ct) + h_masked

    H = hashlib.sha3_256(info_auth + cipher_img.tobytes()).digest()

    signature = mldsa.sign(sk_dsa, H)

    # ---------------- Receiver Side ----------------

    # 1. Verify signature FIRST
    if not mldsa.verify(pk_dsa, H, signature):
        print("Signature INVALID. Abort.")
        sys.exit()

    # 2. Decapsulate
    ss_receiver = ML_KEM_DECAPS(dk, ct)

   
    # 3️⃣ Re-derive everything (Receiver side)
    K_enc2, K_mask2, h_img2, u2, v2, w2, x02, y02, z02 = receiver_key_derivation(
        bytes(ss_receiver),
        bytes(ct),
        h_masked,      # use transmitted masked hash
        pid_S,
        pid_R,
        sid,
        ts
    )

    # 5. Decrypt
    recovered = chaotic_decrypt(cipher_img.copy(), u2, v2, w2, x02, y02, z02)

    # 6. Final integrity check
    if hashlib.sha3_256(recovered.tobytes()).digest() != h_img2:
        print("Integrity Check FAILED")
    else:
        print("Image Recovery Success:",
              np.array_equal(img, recovered))

    Image.fromarray(cipher_img).save("cipher_output.tiff")
    Image.fromarray(recovered).save("recovered_output.tiff")

    print("\nCipher image saved as cipher_output.tiff")
    print("Recovered image saved as recovered_output.tiff")
 