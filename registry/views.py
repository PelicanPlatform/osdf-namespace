from flask_smorest import Blueprint
from flask import request, jsonify, url_for

from registry.models import db, Namespace, NamespaceSchema

# Create a Blueprint for namespace related operations
namespace_blp = Blueprint('namespaces', 'namespaces', url_prefix='/namespaces',
                         description='Operations on namespaces')

# Define endpoint to list all namespaces
@namespace_blp.route('/')
@namespace_blp.response(200, NamespaceSchema(many=True))
def list_namespaces():
    namespaces = Namespace.query.all()
    return namespaces

# Define endpoint to create a new namespace
@namespace_blp.route('/<prefix>', methods=['POST'])
@namespace_blp.arguments(NamespaceSchema)
@namespace_blp.response(201, NamespaceSchema())
def create_namespace(args, prefix):
    print(prefix)
    print(args)
    namespace = Namespace(prefix=prefix, **args)
    db.session.add(namespace)
    db.session.commit()
    return namespace

# Define endpoint to delete a namespace
@namespace_blp.route('/<prefix>', methods=['DELETE'])
@namespace_blp.response(204, description="No content")
def delete_namespace(prefix):
    namespace = Namespace.query.filter_by(prefix=prefix).first()
    if namespace:
        db.session.delete(namespace)
        db.session.commit()

# Define endpoint to get the JWKS for a namespace
@namespace_blp.route('/<prefix>/issuer.jwks')
@namespace_blp.response(200, description="Success")
def get_jwks(prefix):
    namespace = Namespace.query.filter_by(prefix=prefix).first()
    if namespace:
        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "kid": namespace.id,
                    "n": namespace.pubkey,
                    "e": "AQAB"
                }
            ]
        }
        return jsonify(jwks)
    else:
        return jsonify({"message": "Namespace not found."}), 404

# Define endpoint to get the OpenID configuration for a namespace
@namespace_blp.route('/<prefix>/.well-known/openid-configuration')
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