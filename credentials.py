import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def decrypt_password(encrypted_password, key):
    """Decrypts the encrypted password using AES-256-CBC."""
    # Base64 decode the encrypted password to get the IV and encrypted data
    encrypted_data = base64.b64decode(encrypted_password)
    
    # Extract the IV and the actual encrypted password
    iv = encrypted_data[:16]  # The IV is the first 16 bytes
    encrypted = encrypted_data[16:]  # The rest is the encrypted password
    
    # Set up the AES cipher with the key and IV
    cipher = Cipher(algorithms.AES(key.encode()), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # Decrypt the password
    decrypted_password = decryptor.update(encrypted) + decryptor.finalize()
    
    return decrypted_password.decode('utf-8')

def get_scraper_credentials(cursor, decryption_key):
    """Fetch the scraper username and password from the database and decrypt the password."""
    cursor.execute("SELECT username, encrypted_password FROM scraper_accounts WHERE user_id = 1 LIMIT 1;")
    username, encrypted_password = cursor.fetchone()
    
    # Decrypt the password
    decrypted_password = decrypt_password(encrypted_password, decryption_key)
    
    return username, decrypted_password