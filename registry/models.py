from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

db = SQLAlchemy()

class Namespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(128), unique=True, nullable=False)
    pubkey = db.Column(db.String(2048), nullable=False)
    identity = db.Column(db.String(2048), nullable=True)
    admin_metadata = db.Column(db.String(2048), nullable=True)
    # user_metadata = db.Column(db.String(2048), nullable=True)
    
class NamespaceSchema(Schema):
    id = fields.Int(dump_only=True)
    prefix = fields.Str(required=True)
    pubkey = fields.Str(required=True)
    identity = fields.Str(required=False)
    admin_metadata = fields.Str(required=False)
    user_metadata = fields.Str(required=False)

# Define Marshmallow schema for Namespace
class ClientSecondHandshakeSchema(Schema):
    client_nonce = fields.Str(required=True)
    server_nonce = fields.Str(required=True)
    timestamp = fields.Str(required=True)
    pubkey = fields.Str(required=True)
    server_signature = fields.Str(required=True)
    client_signature = fields.Str(required=True)

class ClientFirstHandshakeSchema(Schema):
    client_nonce = fields.Str(required=True)
    pubkey = fields.Str(required=True)
