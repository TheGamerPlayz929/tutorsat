import hashlib
import random

_MASK = (1 << 63) - 1


def derive_seed(*parts) -> int:
    key = ":".join(str(p) for p in parts)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & _MASK


def rng_for(master_seed, *parts):
    return random.Random(derive_seed(master_seed, *parts))
