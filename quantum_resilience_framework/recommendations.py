"""
Migration recommendation engine.

Maps a classified asset (by role and current primitive) to a specific NIST
FIPS-standardised replacement and parameter set, following the security-level
mappings in FIPS 203/204/205.
"""

from .models import AssetRole, QuantumVulnerability

_KEM_REPLACEMENT = {1: "ML-KEM-512", 3: "ML-KEM-768", 5: "ML-KEM-1024"}
_SIG_REPLACEMENT = {1: "ML-DSA-44", 3: "ML-DSA-65", 5: "ML-DSA-87"}
_SIG_BACKUP = {1: "SLH-DSA-SHA2-128s", 3: "SLH-DSA-SHA2-192s", 5: "SLH-DSA-SHA2-256s"}


def _security_level(name: str) -> int:
    """Return an approximate NIST security level (1, 3, or 5) from a primitive name."""
    normalised = name.lower()
    if any(s in normalised for s in ["4096", "p-521", "p521", "256-bit", "aes-256", "sha-512", "sha512"]):
        return 5
    if any(s in normalised for s in ["3072", "p-384", "p384", "192-bit", "aes-192"]):
        return 3
    return 1  # default: RSA-2048, P-256, AES-128, SHA-256 class


def recommend(name: str, role: AssetRole, vulnerability: QuantumVulnerability) -> str:
    """Produce a human-readable migration recommendation for one asset."""
    if vulnerability == QuantumVulnerability.SAFE:
        return f"Already NIST PQC-standardised ({name}). No migration required - monitor for parameter-set updates only."

    level = _security_level(name)

    if vulnerability == QuantumVulnerability.WEAKENED:
        if role == AssetRole.SYMMETRIC_ENCRYPTION:
            if level >= 5:
                return (f"{name} already uses a 256-bit (or larger) key. Grover's algorithm "
                        "still halves its effective security margin, but 256 bits leaves a "
                        "comfortable 128-bit post-quantum margin - no key-size change is needed.")
            return (f"{name} is weakened by Grover's algorithm, not broken. Migrate to a "
                    "256-bit key size (e.g. AES-256) to restore a 128-bit post-quantum "
                    "security margin. No FIPS PQC replacement is needed.")
        if role in (AssetRole.HASH, AssetRole.MAC):
            if level >= 5:
                return (f"{name} already uses a 512-bit (or equivalent) output, which retains "
                        "an adequate post-quantum margin under Grover's algorithm - no change "
                        "is needed.")
            return (f"{name} is weakened by Grover's algorithm. Use a 384-bit or 512-bit "
                    "output (e.g. SHA-384/SHA-512, HMAC-SHA-512) for an adequate "
                    "post-quantum margin.")
        return f"{name} is weakened by Grover's algorithm. Increase output/key size for a post-quantum margin."

    if vulnerability == QuantumVulnerability.UNKNOWN:
        return (f"'{name}' was not recognised by the classifier - this may mean no "
                "cryptographic primitive is in use at all (e.g. a legacy protocol with no "
                "native authentication or encryption), or an unrecognised/misspelled "
                "algorithm name. Manual review is required before a FIPS 203/204/205 "
                "replacement can be recommended.")

    # from here on, vulnerability is definitely BROKEN
    if role == AssetRole.KEY_EXCHANGE:
        kem = _KEM_REPLACEMENT[level]
        return (f"{name} is broken by Shor's algorithm. Recommend {kem} (FIPS 203), or a "
                f"hybrid X25519+{kem} construction during the migration window "
                "(draft-ietf-tls-ecdhe-mlkem) for defence-in-depth.")

    if role == AssetRole.SIGNATURE:
        dsa = _SIG_REPLACEMENT[level]
        backup = _SIG_BACKUP[level]
        return (f"{name} is broken by Shor's algorithm. Recommend {dsa} (FIPS 204) as the "
                f"primary replacement, with {backup} (FIPS 205) as a hash-based backup for "
                "long-lived root-of-trust signatures.")

    return (f"{name} is broken by Shor's algorithm. Role '{role.value}' needs manual "
            "classification to select the correct FIPS 203/204/205 replacement.")
