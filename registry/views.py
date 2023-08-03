from flask_smorest import Blueprint
from flask import request, jsonify, url_for, current_app
import os
import time
import binascii
from registry.models import db, Namespace, NamespaceSchema, ClientFirstHandshakeSchema, ClientSecondHandshakeSchema
from registry.cryp import load_private_key, load_public_key, sign_payload, verify_signature, load_public_key_from_json
import requests
import base64
import json


OIDCClientID = os.getenv('OIDC_CLIENT_ID')
OIDCClientSecret = os.getenv('OIDC_CLIENT_SECRET')

OIDCProviderMetadataURL = "https://cilogon.org/.well-known/openid-configuration"
OIDCScope = "openid profile email"
DeviceAuthEndpoint = "https://cilogon.org/oauth2/device_authorization"
TokenEndpoint = "https://cilogon.org/oauth2/token"
GrantType = "urn:ietf:params:oauth:grant-type:device_code"

def register_a_namespace(data):
    prefix = data.get('prefix')
    pubkey = str(data.get('pubkey'))
    identity = data.get('identity')
    print("Prefix: " + prefix)
    print("Pubkey: " + pubkey)


    if identity:
        print("Identity: " + identity)
        namespace = Namespace(prefix=prefix, pubkey=pubkey, identity=identity)
    else:
        namespace = Namespace(prefix=prefix, pubkey=pubkey)
    db.session.add(namespace)
    db.session.commit()

    return jsonify({
        "status": "Register a new namespace"
    }), 200

def list_all_namespaces(data):
    return jsonify({
        "status": "List all namespaces"
    }), 200

def delete_a_namespace(data):
    return jsonify({
        "status": "Delete a namespace"
    }), 200

def get_a_namespace(data):
    return jsonify({
        "status": "Get a namespace"
    }), 200


def key_sign_challenge(data, action):
    client_nonce = data.get('client_nonce')
    server_nonce = data.get('server_nonce')
    client_pubkey = data.get('pubkey')
    client_payload = data.get('client_payload')
    client_signature = data.get('client_signature')
    server_payload = data.get('server_payload')
    server_signature = data.get('server_signature')

    if client_nonce and server_nonce and client_pubkey and client_payload and client_signature and server_payload and server_signature:
        return key_sign_challenge_commit(data, action)
    elif client_nonce and client_pubkey:
        return key_sign_challenge_init(data)
    else:
        return jsonify({
            "status": "MISSING PARAMETERS"
        }), 300

def key_sign_challenge_init(data):
    client_nonce = data.get('client_nonce')
    server_nonce = os.urandom(32).hex()
    # concatenate client_nonce and server_nonce
    server_payload = client_nonce + server_nonce
    private_key = load_private_key('/key/server.key')
    server_signature = sign_payload(private_key, server_payload)
    return jsonify({
        "server_nonce": server_nonce,
        "client_nonce": client_nonce,
        "server_payload": server_payload,
        "server_signature": server_signature
        }), 200

def key_sign_challenge_commit(data, action):
    client_nonce = data.get('client_nonce')
    server_nonce = data.get('server_nonce')
    json_public_key = data['pubkey']
    client_pubkey = load_public_key_from_json(json_public_key)
    # client_payload = data.get('client_payload')
    client_payload = client_nonce + server_nonce
    client_signature = data.get('client_signature')
    client_verified = verify_signature(client_pubkey, client_payload, client_signature)

    server_payload = data.get('server_payload')
    server_signature = data.get('server_signature')
    server_pubkey = load_public_key('/key/server.jwks')
    server_verified = verify_signature(server_pubkey, server_payload, server_signature)

    
    if client_verified and server_verified:
        if action == "register":
            return register_a_namespace(data)
        elif action == "list":
            return list_all_namespaces(data)
        elif action == "delete":
            return delete_a_namespace(data)
        elif action == "get":
            return get_a_namespace(data)
    else:
        return jsonify({
            "status": "Key Sign Challenge FAILED"
        }), 300

# Create a Blueprint for namespace related operations
namespace_blp = Blueprint('namespaces', 'namespaces', url_prefix='/',
                         description='Operations on namespaces')

@namespace_blp.route('/cli-namespaces/registry', methods=['POST'])
def cli_register_namespace():
    data = request.get_json()
    identity_required = data.get('identity_required')
    device_code = data.get('device_code')
    access_token = data.get('access_token')
    pubkey = data.get('pubkey')
    client_nonce = data.get('client_nonce')

    if access_token:
        payload = {
            "access_token": access_token,
        }
        id_response = requests.post("https://cilogon.org/oauth2/userinfo", data=payload)
        data['identity'] = id_response.text
        print("Identity in register: " + data['identity'])
        return key_sign_challenge(data, "register")
    
    if not identity_required or identity_required == "false":
        return key_sign_challenge(data, "register")
    
    if not device_code:
        payload = {
            "client_id": OIDCClientID,
            "client_secret": OIDCClientSecret,
            "scope": OIDCScope
        }
        response = requests.post(DeviceAuthEndpoint, data=payload)
        response = response.json()
        verification_url_complete = response.get('verification_uri_complete')
        device_code = response.get('device_code')
        payload = {
            "device_code": device_code,
            "verification_url": verification_url_complete
        }
        return jsonify(payload), 200
    else:
        device_code = data.get('device_code')
        payload = {
            "client_id": OIDCClientID,
            "client_secret": OIDCClientSecret,
            "device_code": device_code,
            "grant_type": GrantType,
        }
        response = requests.post(TokenEndpoint, data=payload)
        access_token = response.json().get('access_token')
        if not access_token:
            payload = {
                "status": "PENDING",
            }
            
        else:
            payload = {
                "status": "APPROVED",
                "access_token": access_token
            }

        return jsonify(payload), 200


# Define CLI endpoint to list all namespaces
@namespace_blp.route('/cli-namespaces')
@namespace_blp.response(200, NamespaceSchema(many=True))
def cli_list_namespaces():
    namespaces = Namespace.query.all()
    return namespaces

# Define endpoint to get the JWKS for a namespace
@namespace_blp.route('/cli-namespaces/<prefix>/issuer.jwks')
@namespace_blp.response(200, description="Success")
def get_jwks(prefix):
    namespace = Namespace.query.filter_by(prefix=prefix).first()
    # Replace single quotes with double quotes to make it a valid JSON format

    if namespace:
        pubkey_str = namespace.pubkey
        pubkey_str = pubkey_str.replace("'", '"')
        pubkey_dict = json.loads(pubkey_str)
        jwks = {
            "keys": [
                pubkey_dict
            ]
        }
        return jsonify(jwks)
    else:
        return jsonify({"message": "Namespace not found."}), 404

# Define endpoint to get the OpenID configuration for a namespace
@namespace_blp.route('/cli-namespaces/<prefix>/.well-known/openid-configuration')
@namespace_blp.response(200, description="Success")
def get_openid_configuration(prefix):
    namespace = Namespace.query.filter_by(prefix=prefix).first()
    if namespace:
        issuer_url = url_for("namespaces.get_jwks", prefix=prefix, _external=True)
        openid_config = {
            "issuer": f"http://{request.host}/namespaces/{prefix}",
            "jwks_uri": issuer_url,
            # Add more OpenID configuration metadata as needed
        }
        # Return the openid configuration data if namespace is found
        return jsonify(openid_config)
    else:
        # Return error message if namespace is not found
        return jsonify({"message": "Namespace not found."}), 404

# Define endpoint to delete a namespace
@namespace_blp.route('/cli-namespaces/<prefix>', methods=['DELETE'])
@namespace_blp.response(204, description="No content")
def delete_namespace(prefix):
    namespace = Namespace.query.filter_by(prefix=prefix).first()

    if namespace:
        db.session.delete(namespace)
        db.session.commit()

# # Define endpoint to list all namespaces
# @namespace_blp.route('/namespaces')
# @namespace_blp.response(200, NamespaceSchema(many=True))
# def list_namespaces():
#     namespaces = Namespace.query.all()
#     return namespaces

# # Define endpoint to create a new namespace
# @namespace_blp.route('/namespaces/<prefix>/verify', methods=['POST'])
# @namespace_blp.arguments(ClientFirstHandshakeSchema)
# def verify_signature(args, prefix):
#     args = request.get_json()

#     # Check if client nonce and public key are provided
#     if 'client_nonce' not in args or 'pubkey' not in args:
#         return {"error": "client_nonce and pubkey are required"}, 400

#     # generate a server nonce
#     server_nonce = os.urandom(32).hex()

#     # get the current timestamp
#     timestamp = str(time.time())

#     # get the server's private key
#     private_key = current_app.config['PRIVATE_KEY']

#     # concatenate the nonces, timestamp and public key and sign them
#     client_nonce = args['client_nonce']
#     client_pubkey = args['pubkey']
#     data_to_sign = client_nonce + server_nonce + timestamp + client_pubkey
#     server_signature = sign_data(data_to_sign.encode(), private_key)

#     return jsonify({
#         'client_nonce': client_nonce,
#         'server_nonce': server_nonce,
#         'timestamp': timestamp,
#         'pubkey': client_pubkey,
#         'server_signature': server_signature
#     })

# Define endpoint to create a new namespace
# @namespace_blp.route('/namespaces/<prefix>', methods=['POST'])
# @namespace_blp.arguments(ClientSecondHandshakeSchema)
# @namespace_blp.response(201, NamespaceSchema())
# def create_namespace(args, prefix):
#     args = request.get_json()
#     if 'client_nonce' not in args or 'server_nonce' not in args or 'timestamp' not in args or 'pubkey' not in args or 'server_signature' not in args or 'client_signature' not in args:
#         return {"error": "client_nonce, server_nonce, timestamp, pubkey, server_signature and client_signature are required"}, 400
    
#     client_pubkey = args['pubkey']
#     client_signature = args['client_signature']
#     client_nonce = args['client_nonce']
#     server_nonce = args['server_nonce']
#     timestamp = args['timestamp']

#     client_data_to_verify = client_nonce + server_nonce
#     client_signature = binascii.unhexlify(args['client_signature'])
#     if not verify_data(client_data_to_verify, client_signature, client_pubkey):
#         return {"error": "client_signature is invalid"}, 400

#     server_data_to_verify = client_nonce + server_nonce + timestamp + client_pubkey
#     server_signature = binascii.unhexlify(args['server_signature'])
#     server_pubkey = current_app.config['PUBLIC_KEY'].decode()

#     if not verify_data(server_data_to_verify, server_signature, server_pubkey):
#         return {"error": "server_signature is invalid"}, 400

#     namespace = Namespace(prefix=prefix, pubkey=client_pubkey)
#     db.session.add(namespace)
#     db.session.commit()
#     return namespace





