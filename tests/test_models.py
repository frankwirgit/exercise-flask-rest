# License info goes here.

"""
Test cases for Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convinient to use this:
    nosetests --stop tests/test_models.py:TestPatModel

"""
import os
import logging
import unittest
from werkzeug.exceptions import NotFound
from service.models import Pat, Gender, DataValidationError, db
from service import app
#from .factories import PatFactory
from datetime import datetime
import json

#read the sample jason to dictionary list and provide for test
with open('tests/records.json') as jsonfile:
    sample_data = json.load(jsonfile)
#Q: print(sample_data[0]["lname"])

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

######################################################################
#  MODEL TEST CASES
######################################################################
class TestPatModel(unittest.TestCase):
    """ Test Cases for Model """

    @classmethod
    def setUpClass(cls):
        """ These run once per Test suite """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Pat.init_db(app)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_a_pat(self):
        """ Create a patient and assert that it exists """
        pat = Pat(title="Ms.", fname="Daisy", lname="Dog", street="2000 Highland", postal_code="98765", city="Hayward", state="CA", phone_home="(510) 793-9896", email="dog@us.ibm.com", DOB=datetime.strptime('2010-10-09', "%Y-%m-%d"), gender=Gender.Female)
        self.assertTrue(pat != None)
        self.assertEqual(pat.id, None)
        self.assertEqual(pat.fname, "Daisy")
        self.assertEqual(pat.postal_code, "98765")
        self.assertEqual(pat.city, "Hayward")
        self.assertEqual(pat.gender, Gender.Female)
        self.assertEqual(pat.DOB, datetime.strptime('2010-10-09', "%Y-%m-%d"))

    def test_add_a_pat(self):
        """ Create a patient and add it to the database """
        pats = Pat.all()
        self.assertEqual(pats, [])
        pat = Pat(title="Mr.", fname="Sweetheart", lname="Cat", street="2001 Highland", postal_code="98764", city="Los Angeles", state="CA", phone_home="(310) 893-9845", email="cat@us.ibm.com", DOB=datetime.strptime('2019-12-31', "%Y-%m-%d"), gender=Gender.Male)
        self.assertTrue(pat != None)
        self.assertEqual(pat.id, None)
        pat.create()
        # Asert that it was assigned an id and shows up in the database
        self.assertEqual(pat.id, 1)
        pats = Pat.all()
        self.assertEqual(len(pats), 1)

    def test_update_a_pat(self):
        """ Update a patient """
        pat = Pat()
        pat = pat.deserialize(sample_data[0])
        logging.debug(pat)
        pat.create()
        logging.debug(pat)
        self.assertEqual(pat.id, 1)
        # Change it an save it
        pat.postal_code = "97600"
        original_id = pat.id
        pat.save()
        self.assertEqual(pat.id, original_id)
        self.assertEqual(pat.postal_code, "97600")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        pats = Pat.all()
        self.assertEqual(len(pats), 1)
        self.assertEqual(pats[0].id, 1)
        self.assertEqual(pats[0].postal_code, "97600")

    def test_delete_a_pat(self):
        """ Delete a patient """
        #pat = PatFactory()
        pat = Pat()
        pat = pat.deserialize(sample_data[1])
        pat.create()
        self.assertEqual(len(Pat.all()), 1)
        # delete the patient and make sure doesn't exist in the database
        pat.delete()
        self.assertEqual(len(Pat.all()), 0)

    def test_serialize_a_pat(self):
        """ Test serialization of a patient """
        #pat = PatFactory()
        pat = Pat()
        pat = pat.deserialize(sample_data[2])
        data = pat.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], pat.id)
        self.assertIn("fname", data)
        self.assertEqual(data["fname"], pat.fname)
        self.assertIn("lname", data)
        self.assertEqual(data["lname"], pat.lname)
        self.assertIn("postal_code", data)
        self.assertEqual(data["postal_code"], pat.postal_code)
        self.assertIn("phone_home", data)
        self.assertEqual(data["phone_home"], pat.phone_home)
        self.assertIn("DOB", data)
        self.assertEqual(data["DOB"], pat.DOB.strftime("%Y-%m-%d"))
        self.assertIn("sex", data)
        self.assertEqual(data["sex"], pat.gender.name)

    def test_deserialize_a_pat(self):
        """ Test deserialization of a patient """
        #sample_data[3] = 
        # {'title': 'Mr.', 'fname': 'Richard', 'mname': 'Cortez', 'lname': 'Jones', 'street': '400 West Broadway', 'postal_code': '92101', 'city': 'San Diego', 'state': 'CA', 'phone_home': '(619) 555-5555', 'email': 'richard@pennfirm.com', 'DOB': '1940-12-16', 'sex': 'Male'}
        pat = Pat()
        pat.deserialize(sample_data[3])
        self.assertNotEqual(pat, None)
        self.assertEqual(pat.id, None)
        self.assertEqual(pat.fname, "Richard")
        self.assertEqual(pat.street, "400 West Broadway")
        self.assertEqual(pat.state, "CA")
        self.assertEqual(pat.email, "richard@pennfirm.com")
        self.assertEqual(pat.gender, Gender.Male)

    def test_deserialize_missing_data(self):
        """ Test deserialization of a patient with missing required value """
        #miss the required first name
        data = {'title': 'Mr.', 'mname': 'Alexis', 'lname': 'Jenane', 'street': '145 N. East Street', 'postal_code': '92111', 'city': 'La Mesa', 'state': 'CA', 'phone_home': '(619) 555-2222', 'email': 'i.jenane@email.com', 'DOB': '1933-03-22', 'sex': 'Female'}
        pat = Pat()
        self.assertRaises(DataValidationError, pat.deserialize, data)

    def test_deserialize_bad_data(self):
        """ Test deserialization of a patient with bad data """
        #assign a wrong zip code
        data = {'title': 'Mr.', 'mname': 'Alexis', 'lname': 'Jenane', 'street': '145 N. East Street', 'postal_code': '921155', 'city': 'La Mesa', 'state': 'CA', 'phone_home': '(619) 555-2222', 'email': 'i.jenane@email.com', 'DOB': '1933-03-22', 'sex': 'Female'}
        pat = Pat()
        self.assertRaises(DataValidationError, pat.deserialize, data)

    def test_find_pat(self):
        """ Find a patient by ID """
        #pats = PatFactory.create_batch(3)
        pats = [Pat() for i in range(3)]
        for idx, pat in enumerate(pats):
            pat = pat.deserialize(sample_data[idx])
            pat.create()
        logging.debug(pats)
        # make sure they got saved
        self.assertEqual(len(Pat.all()), 3)
        # find the 2nd patient in the list
        pat = Pat.find(pats[1].id)
        self.assertIsNot(pat, None)
        self.assertEqual(pat.id, pats[1].id)
        self.assertEqual(pat.fname, pats[1].fname)
        self.assertEqual(pat.city, pats[1].city)

    def test_find_by_lname(self):
        """ Find patients by last name """
        for i in range(4):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()

        pats = Pat.find_by_lname("Moses")
        self.assertEqual(pats[0].lname, "Moses")
        self.assertEqual(pats[0].fname, "Jim")
        self.assertEqual(pats[0].phone_home, "(323) 555-4444")

    def test_find_by_fname(self):
        """ Find patients by first name """
        for i in range(4):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()

        pats = Pat.find_by_fname("Nora")
        self.assertEqual(pats[0].fname, "Nora")
        self.assertEqual(pats[0].lname, "Cohen")
        self.assertEqual(pats[0].phone_home, "(213) 555-5555")

    def test_find_by_phone(self):
        """ Find patients by home phone number """
        for i in range(4):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()

        pats = Pat.find_by_phone("(213) 555-5555")
        self.assertEqual(pats[0].fname, "Nora")
        self.assertEqual(pats[0].lname, "Cohen")
        self.assertEqual(pats[0].phone_home, "(213) 555-5555")

    def test_find_by_zip(self):
        """ Find patients by zip code """
        for i in range(4):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()

        pats = Pat.find_by_zip("92101")
        self.assertEqual(pats[0].fname, "Nora")
        self.assertEqual(pats[0].lname, "Cohen")
        self.assertEqual(pats[0].postal_code, "92101")


    def test_find_by_gender(self):
        """ Find patients by gender """
        for i in range(7):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()

        pats = Pat.find_by_gender(Gender.Female)
        pat_list = [pat for pat in pats]
        self.assertEqual(len(pat_list), 2)
        self.assertEqual(pats[1].fname, "Ilias")
        self.assertEqual(pats[1].lname, "Jenane")
        pats = Pat.find_by_gender(Gender.Male)
        pat_list = [pat for pat in pats]
        self.assertEqual(len(pat_list), 5)

    def test_find_or_404_found(self):
        """ Find or return 404 found """
        #pats = PatFactory.create_batch(3)
        pats = []
        for i in range(4):
            pat = Pat()
            pat = pat.deserialize(sample_data[i])
            pat.create()
            pats.append(pat)
        
        pat = Pat.find_or_404(pats[1].id)
        self.assertIsNot(pat, None)
        self.assertEqual(pat.id, pats[1].id)
        self.assertEqual(pat.lname, pats[1].lname)
        self.assertEqual(pat.fname, pats[1].fname)
        self.assertEqual(pat.DOB, pats[1].DOB)

    def test_find_or_404_not_found(self):
        """ Find or return 404 NOT found """
        self.assertRaises(NotFound, Pat.find_or_404, 0)
