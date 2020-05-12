# License info goes here.

"""
Models for Patient Membership Data

All of the models are stored in this module

Models
------
Pat - A patient in membership list

Attributes:
-----------
title (string) - the title of a patient
fname (string), mname (string), lname (string) - the first, middle and last name of a patient
Primary address - to do: seperate as a foreign table
    street (string), 
    postal_code (int), use re to validate, 
    city (string), 
    state (string) 
phone_home (string) - the home phone number of a patient, use re to validate
email (string) - the email of a patient, use package to validate
DOB (DateTime) - the date of birth of a patient, use datetime() to validate
gender (enum) - Male, Female or Unknown
* category (string) - the category the patient belongs to (i.e., in, out)
* eligibility (boolean) - True or False

"""
import logging
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
import re
#pip install email_validator
from email_validator import validate_email, EmailNotValidError
from datetime import datetime

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()

# Zip code mapping with regular expression
zipCode = re.compile(r"^[0-9]{5}(?:-[0-9]{4})?$")
phoneNumb = re.compile(r"^\([0-9]{3}\)\s*[0-9]{3}-[0-9]{4}$")


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass

class Gender(Enum):
    """ Enumeration of valid Genders """
    Male = 1
    Female = 2
    Unknown = 3

#Base model class
class Pat(db.Model):
    """
    Class that represents a Patient

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    app = None

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=True)
    fname = db.Column(db.String(60), nullable=False)
    mname = db.Column(db.String(60), nullable=True)
    lname = db.Column(db.String(60), nullable=False)
    street = db.Column(db.String(60), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(40), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    phone_home = db.Column(db.String(14), nullable=False)
    email = db.Column(db.String(60), nullable=True)
    DOB = db.Column(db.DateTime, nullable=False)
    #DOB = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gender = db.Column(db.Enum(Gender), nullable=False, server_default=(Gender.Unknown.name))
    #category = db.Column(db.String(63), nullable=False)
    #eligibility = db.Column(db.Boolean(), nullable=False, default=True)
    
    def __repr__(self):
        return "<Pat fname=%r lname=%r id=[%s]>" % (self.fname, self.lname, self.id)

    def create(self):
        """
        Creates a new Pat to the database
        """
        logger.info("Creating %s %s", self.fname, self.lname)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def save(self):
        """
        Updates an existing Pat to the database
        """
        logger.info("Saving %s %s", self.fname, self.lname)
        db.session.commit()

    def delete(self):
        """ Removes a Pat from the data store """
        logger.info("Deleting %s %s", self.fname, self.lname)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a Pat into a dictionary """
        return {
            "id": self.id,
            "title": self.title,
            "fname": self.fname,
            "mname": self.mname,
            "lname": self.lname,
            "street": self.street,
            "postal_code": self.postal_code,
            "city": self.city,
            "state": self.state,
            "phone_home": self.phone_home,
            "email": self.email,
            "DOB": self.DOB.strftime("%Y-%m-%d"),
            "sex": self.gender.name, # convert enum to string
            #"category": self.category,
            #"eligibility": self.eligibility,
            
        }

    def deserialize(self, data):
        """
        Deserializes a Pat from a dictionary

        Args:
            data (dict): A dictionary containing the Pat data
        """
        try:
            self.title = data.get("title")
            self.fname = data["fname"]
            self.mname = data.get("mname")
            self.lname = data["lname"]
            self.street = data["street"]

            #validate the zip code
            if zipCode.match(data["postal_code"]):
                self.postal_code = data["postal_code"]
            else:
                raise DataValidationError("Invalid postal code")

            self.city = data["city"]
            self.state = data["state"]

            #validate the phone number
            if phoneNumb.match(data["phone_home"]):
                self.phone_home = data["phone_home"]
            else:
                raise DataValidationError("Invalid home phone")

            #validate the email address
            self.email = None
            if(data.get("email")):
                self.email = validate_email(data.get("email")).email
            
            #validate the DOB
            self.DOB = datetime.strptime(data["DOB"], "%Y-%m-%d")

            self.gender = getattr(Gender, data["sex"])   # create enum from string

            #self.category = data["category"]
            #self.eligibility = data["eligibility"]
        
        except KeyError as error:
            raise DataValidationError("Invalid patient: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError("Invalid patient: body of request contained bad or no data")
        except EmailNotValidError as error:
            raise DataValidationError("Invalid email address")
        except ValueError as error:
            raise DataValidationError("Invalid date value or format")
        return self

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the Pats in the database """
        logger.info("Processing all Pats")
        return cls.query.all()

    @classmethod
    def find(cls, pat_id):
        """ Finds a Pat by the ID """
        logger.info("Processing lookup for id %s ...", pat_id)
        return cls.query.get(pat_id)

    @classmethod
    def find_or_404(cls, pat_id):
        """ Find a Pat by the ID and return Not Found status code """
        logger.info("Processing lookup or 404 for id %s ...", pat_id)
        return cls.query.get_or_404(pat_id)

    @classmethod
    def find_by_lname(cls, lname):
        """ Returns all Pats with the given name

        Args:
            name (string): the last name of Pats you want to match
        """
        logger.info("Processing name query for %s ...", lname)
        return cls.query.filter(cls.lname == lname)

    @classmethod
    def find_by_fname(cls, fname):
        """ Returns all Pats with the given name

        Args:
            name (string): the first name of Pats you want to match
        """
        logger.info("Processing name query for %s ...", fname)
        return cls.query.filter(cls.fname == fname)

    @classmethod
    def find_by_phone(cls, phone_home):
        """ Returns the Pat having the home phone number

        Args:
            phone_home (string): the home phone of the Pat you want to match
        """
        logger.info("Processing phone query for %s ...", phone_home)
        return cls.query.filter(cls.phone_home== phone_home)

    @classmethod
    def find_by_zip(cls, postal_code):
        """ Returns all of the Pats having the zip code

        Args:
            postal_code (string): the zip code of the Pat you want to match
        """
        logger.info("Processing zip code query for %s ...", postal_code)
        return cls.query.filter(cls.postal_code == postal_code)


    @classmethod
    def find_by_category(cls, category):
        """ Returns all of the Pats in a category

        Args:
            category (string): the category of the Pats you want to match
        """
        logger.info("Processing category query for %s ...", category)
        return cls.query.filter(cls.category == category)

    @classmethod
    def find_by_eligibility(cls, eligibility=True):
        """ Returns all Pats by their eligibility

        Args:
            eligibility (boolean): True for Pats that are eligible
        """
        logger.info("Processing eligibility query for %s ...", eligibility)
        return cls.query.filter(cls.eligibility == eligibility)

    @classmethod
    def find_by_gender(cls, gender=Gender.Unknown):
        """ Returns all Pats by their Gender

        Args:
            Gender (enum): Options are ['Male', 'Female', 'Unknown']
        """
        logger.info("Processing gender query for %s ...", gender.name)
        return cls.query.filter(cls.gender == gender)
