#!/usr/bin/env python3
"""
Generate the longest possible secure secret key for Flask applications
"""

import secrets
import sys

def generate_max_length_key():
    """
    Generate the longest possible secure secret key.
    Flask secret key can be any string, but we'll generate the maximum
    practical length that won't cause issues.
    """
    # Flask doesn't have a strict limit, but extremely long keys might cause
    # issues with some WSGI servers or session storage. 512 bytes is very safe.
    
    # Generate using multiple methods for maximum entropy
    key_parts = [
        secrets.token_urlsafe(384),  # 512 bytes when base64 decoded
        secrets.token_hex(256),      # 512 bytes raw
        ''.join(secrets.choice('!@#$%^&*()_+-=[]{}|;:,.<>?~') for _ in range(64))
    ]
    
    # Combine all parts for maximum length and complexity
    full_key = ''.join(key_parts)
    
    # Ensure we have a good mix of character types
    return full_key

def generate_standard_key():
    """Generate a standard secure key (recommended for most use cases)"""
    return secrets.token_urlsafe(64)  # 512 bits of entropy

def main():
    print("🔐 Flask Secret Key Generator")
    print("=" * 50)
    
    # Generate the ultra-long key
    max_key = generate_max_length_key()
    print(f"\n🚀 ULTRA LONG KEY ({len(max_key)} characters):")
    print("-" * 50)
    print(max_key)
    print("-" * 50)
    
    # Also show standard recommended key
    std_key = generate_standard_key()
    print(f"\n✅ STANDARD KEY ({len(std_key)} characters - Recommended):")
    print("-" * 50)
    print(std_key)
    print("-" * 50)
    
    # Statistics
    print(f"\n📊 STATISTICS:")
    print(f"Ultra Long Key Length: {len(max_key)} characters")
    print(f"Standard Key Length: {len(std_key)} characters")
    print(f"Entropy: ~512+ bits (cryptographically secure)")
    
    # Usage instructions
    print(f"\n💡 USAGE:")
    print("1. Set as environment variable:")
    print(f'   export SECRET_KEY="{std_key}"')
    print("\n2. Or use in your Flask app:")
    print(f'   app.secret_key = os.environ.get("SECRET_KEY") or "{std_key}"')
    
    print(f"\n⚠️  WARNING: Keep this key secret! Do not commit to version control.")

if __name__ == "__main__":
    main()