
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64




def serialize_public_key(public_key):
    public_key_hex = public_key.export_key(format='PEM').decode()
    return public_key_hex

def serialize_private_key(private_key):
    private_key_hex = private_key.export_key(format='PEM', pkcs=1).decode()
    return private_key_hex

def deserialize_public_key(public_key_hex):
    public_key = RSA.import_key(public_key_hex)
    return public_key

def deserialize_private_key(private_key_hex):
    private_key = RSA.import_key(private_key_hex)
    return private_key

def hash_me(public_key):
    hash_object = hashlib.sha256()
    hash_object.update(public_key)
    hash_key = hash_object.hexdigest()
    return hash_object, hash_key

def encrypt_data(data, public_key):
    try:
        if isinstance(data, str):
            data = data.encode()
        cipher = PKCS1_OAEP.new(public_key)
        encrypted_data = cipher.encrypt(data)
        return base64.b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        print(f"Encryption failed: {e}")
        return None

def decrypt_data(encrypted_data, private_key):
    try:
        encrypted_data = base64.b64decode(encrypted_data.encode('utf-8'))
        cipher = PKCS1_OAEP.new(private_key)
        decrypted_data = cipher.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

def generate_key_pair():
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()
    return private_key, public_key

def generate_merkle_tree(data):
    tree = []
    for i in range(0, len(data), 2):
        if i+1 < len(data):
            tree.append(hashlib.sha256(data[i].encode() + data[i+1].encode()).hexdigest())
        else:
            tree.append(data[i])
    return tree

def verify_merkle_tree(tree, root):
    for i in range(0, len(tree)):
        if i+1 < len(tree):
            root = hashlib.sha256(tree[i].encode() + tree[i+1].encode()).hexdigest()
        else:
            return tree[i] == root
    return False

