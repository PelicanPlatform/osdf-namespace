from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

db = SQLAlchemy()

class Namespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(128), unique=True, nullable=False)
    pubkey = db.Column(db.String(2048), nullable=False)
    identity = db.Column(db.String(128), nullable=True)
    admin_metadata = db.Column(db.String(2048), nullable=True)
    user_metadata = db.Column(db.String(2048), nullable=True)

# Define Marshmallow schema for Namespace
class NamespaceSchema(Schema):
    id = fields.Int(dump_only=True)
    prefix = fields.Str()
    pubkey = fields.Str(required=True)
    identity = fields.Str()
    admin_metadata = fields.Str()
    user_metadata = fields.Str()