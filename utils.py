from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request

def api_response(data=None, message="Success", code=200, error=None):
    response = {
        "code": code,
        "message": message,
        "data": data
    }
    if error:
        response["error"] = error
    return jsonify(response), code

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper