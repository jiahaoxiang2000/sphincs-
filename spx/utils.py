# from spx.wots import SPX_N
# from Crypto.Hash import SHA256
SPX_N = 16  # Hash output length in bytes

state_seeded = bytearray(40)  # 32 bytes hash state + 8 bytes counter

# Initialize SHA256 IV constants
IV_256 = bytes(
    [
        0x6A,
        0x09,
        0xE6,
        0x67,
        0xBB,
        0x67,
        0xAE,
        0x85,
        0x3C,
        0x6E,
        0xF3,
        0x72,
        0xA5,
        0x4F,
        0xF5,
        0x3A,
        0x51,
        0x0E,
        0x52,
        0x7F,
        0x9B,
        0x05,
        0x68,
        0x8C,
        0x1F,
        0x83,
        0xD9,
        0xAB,
        0x5B,
        0xE0,
        0xCD,
        0x19,
    ]
)


def rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def ch(x: int, y: int, z: int) -> int:
    return (x & y) ^ (~x & z)


def maj(x: int, y: int, z: int) -> int:
    return (x & y) ^ (x & z) ^ (y & z)


def sigma0(x: int) -> int:
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22)


def sigma1(x: int) -> int:
    return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25)


def gamma0(x: int) -> int:
    return rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3)


def gamma1(x: int) -> int:
    return rotr(x, 17) ^ rotr(x, 19) ^ (x >> 10)


def load_bigendian_32(x: bytes) -> int:
    return int.from_bytes(x[:4], byteorder="big")


def store_bigendian_32(val: int) -> bytes:
    return val.to_bytes(4, byteorder="big")


def crypto_hashblocks_sha256(
    statebytes: bytearray, input_data: bytes, inlen: int
) -> int:
    K = [
        0x428A2F98,
        0x71374491,
        0xB5C0FBCF,
        0xE9B5DBA5,
        0x3956C25B,
        0x59F111F1,
        0x923F82A4,
        0xAB1C5ED5,
        0xD807AA98,
        0x12835B01,
        0x243185BE,
        0x550C7DC3,
        0x72BE5D74,
        0x80DEB1FE,
        0x9BDC06A7,
        0xC19BF174,
        0xE49B69C1,
        0xEFBE4786,
        0x0FC19DC6,
        0x240CA1CC,
        0x2DE92C6F,
        0x4A7484AA,
        0x5CB0A9DC,
        0x76F988DA,
        0x983E5152,
        0xA831C66D,
        0xB00327C8,
        0xBF597FC7,
        0xC6E00BF3,
        0xD5A79147,
        0x06CA6351,
        0x14292967,
        0x27B70A85,
        0x2E1B2138,
        0x4D2C6DFC,
        0x53380D13,
        0x650A7354,
        0x766A0ABB,
        0x81C2C92E,
        0x92722C85,
        0xA2BFE8A1,
        0xA81A664B,
        0xC24B8B70,
        0xC76C51A3,
        0xD192E819,
        0xD6990624,
        0xF40E3585,
        0x106AA070,
        0x19A4C116,
        0x1E376C08,
        0x2748774C,
        0x34B0BCB5,
        0x391C0CB3,
        0x4ED8AA4A,
        0x5B9CCA4F,
        0x682E6FF3,
        0x748F82EE,
        0x78A5636F,
        0x84C87814,
        0x8CC70208,
        0x90BEFFFA,
        0xA4506CEB,
        0xBEF9A3F7,
        0xC67178F2,
    ]

    # Load state
    state = [load_bigendian_32(statebytes[i : i + 4]) for i in range(0, 32, 4)]

    while inlen >= 64:
        # Load block into W
        W = [load_bigendian_32(input_data[i : i + 4]) for i in range(0, 64, 4)]

        # Extend the sixteen 32-bit words into sixty-four 32-bit words
        for i in range(16, 64):
            W.append(
                (gamma1(W[i - 2]) + W[i - 7] + gamma0(W[i - 15]) + W[i - 16])
                & 0xFFFFFFFF
            )

        # Initialize working variables
        a, b, c, d, e, f, g, h = state

        # Main loop
        for i in range(64):
            T1 = (h + sigma1(e) + ch(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
            T2 = (sigma0(a) + maj(a, b, c)) & 0xFFFFFFFF
            h = g
            g = f
            f = e
            e = (d + T1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (T1 + T2) & 0xFFFFFFFF

        # Update state
        state = [(x + y) & 0xFFFFFFFF for x, y in zip(state, [a, b, c, d, e, f, g, h])]

        input_data = input_data[64:]
        inlen -= 64

    # Store state back
    for i, s in enumerate(state):
        statebytes[i * 4 : (i + 1) * 4] = store_bigendian_32(s)

    return inlen


def seed_state(pub_seed: bytes) -> None:
    # Initialize state with IV
    state_seeded[0:32] = IV_256
    count = state_seeded[32:40]
    # transform the counter to integer
    count = int.from_bytes(count, byteorder="big")

    # Prepare input block
    block = bytearray(64)  # SPX_SHA256_BLOCK_BYTES
    block[0:SPX_N] = pub_seed[0:SPX_N]
    # Rest of block remains zero

    # Update state with block
    crypto_hashblocks_sha256(state_seeded, block, 64)
    count += 64
    state_seeded[32:40] = count.to_bytes(8, byteorder="big")
