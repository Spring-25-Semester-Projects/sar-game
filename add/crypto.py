import random
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class SimpleCrypto:
    @staticmethod
    def encrypt(message: str) -> tuple:
        """Enhanced encryption with better error handling"""
        try:
            # Ensure message is uppercase for consistency
            message = message.upper()
            
            # Generate random key
            key = bytes([random.randint(0, 255) for _ in range(32)])
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC)
            
            # Pad and encrypt
            ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
            iv = cipher.iv
            
            # Combine IV and ciphertext
            encrypted = base64.b64encode(iv + ct_bytes).decode()
            return key, encrypted
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return None, None

    @staticmethod
    def decrypt(key: bytes, encrypted: str) -> str:
        """Enhanced decryption with error handling"""
        try:
            # Decode base64
            decoded = base64.b64decode(encrypted)
            
            # Split IV and ciphertext
            iv = decoded[:AES.block_size]
            ct = decoded[AES.block_size:]
            
            # Create cipher and decrypt
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            
            return pt.decode()
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return "DECRYPTION FAILED"