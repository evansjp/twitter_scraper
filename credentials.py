import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def decrypt_password(encrypted_password, encryption_key):
    """Decrypt the password using AES-256-CBC, matching the Rails implementation."""
    # Decode the base64-encoded encrypted data
    encrypted_data = base64.b64decode(encrypted_password)
    
    # Extract the IV (first 16 bytes) and the actual encrypted password
    iv = encrypted_data[:16]
    encrypted = encrypted_data[16:]

    # Set up the AES cipher with the key and IV
    cipher = Cipher(algorithms.AES(bytes.fromhex(encryption_key)), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Decrypt the password
    decrypted_password = decryptor.update(encrypted) + decryptor.finalize()

    # Remove PKCS7 padding
    pad = decrypted_password[-1]
    if isinstance(pad, int):
        decrypted_password = decrypted_password[:-pad]

    return decrypted_password.decode('utf-8')

def get_scraper_credentials(cursor, decryption_key, user_id):
    """Fetch the scraper credentials for a specific user."""
    cursor.execute("SELECT username, email, encrypted_password FROM scraper_accounts WHERE user_id = %s LIMIT 1;", (user_id,))
    credentials = cursor.fetchone()
    if credentials:
        username, email, encrypted_password = credentials
        password = decrypt_password(encrypted_password, decryption_key)
        return username, email, password
    return None, None, None