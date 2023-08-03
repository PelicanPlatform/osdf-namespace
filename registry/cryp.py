from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import base64
import os
import json
import binascii

def base64url_decode(data):
    padding = b'=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def load_private_key(private_key_path):
    with open(private_key_path, 'rb') as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def load_public_key(jwks_file):
    with open(jwks_file) as f:
        jwks = json.load(f)
    jwk = jwks['keys'][0]
    x = base64url_decode(jwk['x'].encode('utf-8'))
    y = base64url_decode(jwk['y'].encode('utf-8'))
    public_numbers = ec.EllipticCurvePublicNumbers(
        x=int.from_bytes(x, byteorder="big"),
        y=int.from_bytes(y, byteorder="big"),
        curve=ec.SECP521R1()
    )
    public_key = public_numbers.public_key(default_backend())
    return public_key

def load_public_key_from_json(json_public_key):
    x = int(json_public_key['x'])
    y = int(json_public_key['y'])
    public_numbers = ec.EllipticCurvePublicNumbers(
        x=x,
        y=y,
        curve=ec.SECP521R1()
    )
    public_key = public_numbers.public_key(default_backend())
    return public_key

def load_signature(signature_file_path):
    with open(signature_file_path, 'rb') as f:
        return f.read()

def sign_payload(private_key, payload):
    payload_bytes = payload.encode('utf-8')
    signature = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
    return binascii.hexlify(signature).decode()

def write_signature(signature, file_path):
    with open(file_path, 'wb') as f:
        f.write(signature)

def verify_signature(public_key, payload, signature):
    signature_bytes = binascii.unhexlify(signature)
    payload_bytes = payload.encode('utf-8')
    try:
        public_key.verify(signature_bytes, payload_bytes, ec.ECDSA(hashes.SHA256()))
        print("Signature is valid.")
        return True
    except InvalidSignature:
        print("Invalid signature.")
        return False

def main():
    private_key = load_private_key('/Users/yqu/Desktop/Workspace/Pelican/pelican-registry-cli/cmd/server.key')  # replace with your private key path
    public_key = load_public_key('/Users/yqu/Desktop/Workspace/Pelican/pelican-registry-cli/cmd/export/.well-known/server.jwks')  # replace with your 
    payload = b"a message to be signed"
    signature = sign_payload(private_key, payload)
    verify_signature(public_key, payload, signature)
    write_signature(signature, './python_signature')  # replace './signature' with the desired file path
    python_signature = load_signature('./python_signature')  # replace './signature' with the desired file path
    verify_signature(public_key, payload, python_signature)
    
    go_signature = load_signature('./go_signature')  # replace './signature' with the desired file path
    verify_signature(public_key, payload, go_signature)

if __name__ == "__main__":
    main()