# License info goes here.

"""
REST API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convinient to use this:
    nosetests --stop tests/test_service.py:TestPatServer
"""

import os
import logging
import unittest
import json
#from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from flask_api import status  # HTTP Status Codes
from service.models import Pat, db
from service.service import app, init_db
#from .factories import PatFactory


# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

with open('tests/records.json') as jsonfile:
    sample_data = json.load(jsonfile)

######################################################################
#  SERVICE TEST CASES
######################################################################
class TestPatServer(unittest.TestCase):
    """ REST Server Tests """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        """ Runs before each test """
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _create_pats(self, count):
        """ Factory method to create patients in bulk """
        pats = []
        for i in range(count):
            test_pat = Pat()
            test_pat = test_pat.deserialize(sample_data[i])
            #test_pat.id = i+1
            resp = self.app.post(
                "/pats", json=test_pat.serialize(), content_type="application/json"
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED, "Could not create test patient"
            )
            new_pat = resp.get_json()
            test_pat.id = new_pat["id"]
            pats.append(test_pat)
        return pats

    def test_index(self):
        """ Test the Home Page """
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "Patient Membership REST API Service")

    def test_get_pat_list(self):
        """ Get a list of patients """
        self._create_pats(5)
        resp = self.app.get("/pats")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_get_pat(self):
        """ Get a single patient """
        test_pat = self._create_pats(1)[0]
        # get the id of a patient
        resp = self.app.get(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["mname"], test_pat.mname)

    def test_get_pat_not_found(self):
        """ Get a patient whos not found """
        resp = self.app.get("/pats/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_pat(self):
        """ Create a new patient """
        test_pat = self._create_pats(1)[0]
        #test_pat = PatFactory()
        logging.debug(test_pat)
        resp = self.app.post(
            "/pats", json=test_pat.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)
        # Check the data is correct
        new_pat = resp.get_json()
        self.assertEqual(new_pat["lname"], test_pat.lname, "Last name does not match")
        self.assertEqual(new_pat["fname"], test_pat.fname, "First name does not match")
        self.assertEqual(new_pat["postal_code"], test_pat.postal_code, "Zip code does not match")
        self.assertEqual(new_pat["DOB"], test_pat.DOB.strftime("%Y-%m-%d"), "DOB does not match")
        # Check that the location header was correct
        resp = self.app.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Check the data is correct
        new_pat = resp.get_json()
        self.assertEqual(new_pat["lname"], test_pat.lname, "Last name does not match")
        self.assertEqual(new_pat["fname"], test_pat.fname, "First name does not match")
        self.assertEqual(new_pat["postal_code"], test_pat.postal_code, "Zip code does not match")
        self.assertEqual(new_pat["DOB"], test_pat.DOB.strftime("%Y-%m-%d"), "DOB does not match")

    def test_update_pat(self):
        """ Update an existing patient """
        # create a patient to update
        test_pat = self._create_pats(1)[0]
        #test_pat = PatFactory()
        resp = self.app.post(
            "/pats", json=test_pat.serialize(), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the patient
        new_pat = resp.get_json()
        logging.debug(new_pat)
        new_pat["fname"] = "Daisy"
        new_pat["email"] = "daisy_puppy@k9.com"
        resp = self.app.put(
            "/pats/{}".format(new_pat["id"]),
            json=new_pat,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_pat = resp.get_json()
        self.assertEqual(updated_pat["fname"], "Daisy")
        self.assertEqual(updated_pat["email"], "daisy_puppy@k9.com")

    def test_delete_pat(self):
        """ Delete a patient """
        test_pat = self._create_pats(1)[0]
        resp = self.app.delete(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        # make sure they are deleted
        resp = self.app.get(
            "/pats/{}".format(test_pat.id), content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_pat_list_by_gender(self):
        """ Query patients by gender """
        pats = self._create_pats(10)
        test_gender = pats[0].gender
        gender_pats = [pat for pat in pats if pat.gender.name == test_gender.name]
        resp = self.app.get("/pats", query_string="sex={}".format(quote_plus(test_gender.name)))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), len(gender_pats))
        # check the data just to be sure
        for _dt in data:
            self.assertEqual(_dt["sex"], test_gender.name)
        app.logger.info("run a test for testing query patients with the same gender")

    # @patch('service.models.Pet.find_by_name')
    # def test_bad_request(self, bad_request_mock):
    #     """ Test a Bad Request error from Find By Name """
    #     bad_request_mock.side_effect = DataValidationError()
    #     resp = self.app.get('/pets', query_string='name=fido')
    #     self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    #
    # @patch('service.models.Pet.find_by_name')
    # def test_mock_search_data(self, pet_find_mock):
    #     """ Test showing how to mock data """
    #     pet_find_mock.return_value = [MagicMock(serialize=lambda: {'name': 'fido'})]
    #     resp = self.app.get('/pets', query_string='name=fido')
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
