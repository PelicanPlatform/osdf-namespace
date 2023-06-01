# osdf-namespace
Flask app for managing osdf namespaces

## Overview
The Web application is implemented using [Flask](https://flask.palletsprojects.com/)

## Quickstart: Tesing on localhost
### Prerequisites
- A CILogon OIDC Clinet ID and Secret
- Add `httpd.conf` and `supervisor-apache.conf` to `apache/`

### Run Local Service
```
docker compose build
docker compose up
```

### Debug Local Service 
```
docker exec -it namespace-registry-webapp /bin/bash
```

## Services

### OpenAPI Specification
- `/swagger-ui`: visual documentation of all API

### Restful API
- `GET /namespace`: list all namespaces
- `POST /namespace/<prefix>`: with key as parameter will create an association between the key and prefix.
- `GET /namespace/<prefix>/issuer.jwks`: returns a JWKS including the public key associated with prefix.
- `GET /namespace/<prefix>/.well-known/openid-configuration`: an OpenID configuration metadata endpoint pointing at the corresponding issuer.jwks
- `DELETE /namespace/<prefix>`: If request is signed by corresponding private key, then this removes the association.