# License info goes here.

"""
Patient Membership Data Set

Paths:
------
GET /pats - Returns a list all of the patients
GET /pats/{id} - Returns the patient with a given id number
POST /pats - creates a new patient record in the database
PUT /pats/{id} - updates a patient record in the database
DELETE /pats/{id} - deletes a patient record in the database
"""

import os
import sys
import logging
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound

# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.models import Pat, DataValidationError, Gender

# Import Flask application
from . import app

######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=message
        ),
        status.HTTP_400_BAD_REQUEST,
    )

@app.errorhandler(status.HTTP_401_UNAUTHORIZED)
def access_unauthorized(error):
    """ Handles bad reuests with 401_UNAUTHORIZED """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_401_UNAUTHORIZED, error="Access Unauthorized", message=message
        ),
        status.HTTP_401_UNAUTHORIZED,
    )

@app.errorhandler(status.HTTP_403_FORBIDDEN)
def access_forbidden(error):
    """ Handles bad reuests with 403_FORBIDDEN """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_403_FORBIDDEN, error="Access Forbidden", message=message
        ),
        status.HTTP_403_FORBIDDEN,
    )

@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(status=status.HTTP_404_NOT_FOUND, error="Not Found", message=message),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=message,
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )

@app.errorhandler(status.HTTP_409_CONFLICT)
def resource_state_conflict(error):
    """ Handles bad reuests with 409_CONFLICT """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_409_CONFLICT, error="Resource State Conflict", message=message
        ),
        status.HTTP_409_CONFLICT,
    )

@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=message,
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    message = str(error)
    app.logger.error(message)
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=message,
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


######################################################################
# GET INDEX PAGE
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return (
        jsonify(
            name="Patient Membership REST API Service",
            version="1.0",
            paths=url_for("list_pats", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# LIST ALL PATIENTS - GET
######################################################################
@app.route("/pats", methods=["GET"])
def list_pats():
    """ Returns all of the Pats """
    app.logger.info("Request for patient list")
    pats = []
    
    fname = request.args.get("fname")
    lname = request.args.get("lname")
    phone_home = request.args.get("phone_home")
    postal_code = request.args.get("postal_code")
    sex = request.args.get("sex")

    
    if fname:
        pats = Pat.find_by_fname(fname)
    elif lname:
        pats = Pat.find_by_lname(lname)
    elif phone_home:
        pats = Pat.find_by_phone(phone_home)
    elif postal_code: 
        pats = Pat.find_by_zip(postal_code)
    elif sex:
        pats = Pat.find_by_gender(getattr(Gender, sex))
    else:
        pats = Pat.all()

    results = [pat.serialize() for pat in pats]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PATIENT - GET + ID
######################################################################
@app.route("/pats/<int:pat_id>", methods=["GET"])
def get_pats(pat_id):
    """
    Retrieve a single Pat

    This endpoint will return a Pat based on his id
    """
    app.logger.info("Request for patient with id: %s", pat_id)
    pat = Pat.find(pat_id)
    if not pat:
        raise NotFound("Patient with id '{}' was not found.".format(pat_id))
    return make_response(jsonify(pat.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A NEW PATIENT - POST
######################################################################
@app.route("/pats", methods=["POST"])
def create_pats():
    """
    Creates a Pat
    This endpoint will create a Pat based the data in the body that is posted
    """
    app.logger.info("Request to create a patient")
    check_content_type("application/json")
    pat = Pat()
    pat.deserialize(request.get_json())
    pat.create()
    message = pat.serialize()
    location_url = url_for("get_pats", pat_id=pat.id, _external=True)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# UPDATE AN EXISTING PATIENT - PUT + ID
######################################################################
@app.route("/pats/<int:pat_id>", methods=["PUT"])
def update_pats(pat_id):
    """
    Update a Pat

    This endpoint will update a Pat based the body that is posted
    """
    app.logger.info("Request to update patient with id: %s", pat_id)
    check_content_type("application/json")
    pat = Pat.find(pat_id)
    if not pat:
        raise NotFound("Patient with id '{}' was not found.".format(pat_id))
    pat.deserialize(request.get_json())
    pat.id = pat_id
    pat.save()
    return make_response(jsonify(pat.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE A PATIENT - DELETE + ID
######################################################################
@app.route("/pats/<int:pat_id>", methods=["DELETE"])
def delete_pats(pat_id):
    """
    Delete a Pat

    This endpoint will delete a Pat based the id specified in the path
    """
    app.logger.info("Request to delete the patient with id: %s", pat_id)
    pat = Pat.find(pat_id)
    if pat:
        pat.delete()
    return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
#  UTILITY FUNCTIONS
######################################################################


def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Pat.init_db(app)


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    #HTTP 415 Unsupported Media Type
    abort(415, "Content-Type must be {}".format(content_type))
