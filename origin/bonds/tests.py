import json
import os
from datetime import datetime
import copy as cp

from rest_framework.test import APISimpleTestCase, APITransactionTestCase, APITestCase
from .models import Bond
from .views import BondAPI
from django.contrib.auth import get_user_model

testDataDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"testdata")
TEST_DATA_LIMIT = 10

# Parse test data files
with open(os.path.join(testDataDir, "lei_list.json"), "r", encoding="utf-8") as f:
    testleis = json.load(f)[:TEST_DATA_LIMIT]
with open(os.path.join(testDataDir, "test_bonds.json"), "r", encoding="utf-8") as f:
    data = json.load(f)
    test_bonds = data[:TEST_DATA_LIMIT]


# Called after inserting a record, compares it with the original input bond
def test_db_records():
    for tb in test_bonds:
        tb = cp.deepcopy(tb["exp_output"])
        results = Bond.objects.filter(**tb)
        results = results.values(
            "isin", "size",
            "currency", "maturity",
            "lei", "legal_name"
        )[0]
        tb["maturity"] = datetime.strptime(tb["maturity"],"%Y-%m-%d").date()
        assert results == tb

# Creates user with passed credentials, returns User instance and credentials
def make_fake_user(username, password):
    User = get_user_model()
    user = User.objects.create_user(username, '', password)
    user.save()
    return {"user": user, "username": username, "password": password}


class LegalNameTest(APISimpleTestCase):
    def test_legal_name(self):
        print("Testing LegalName (May take a while)")
        for tl in testleis:
            assert BondAPI.get_legal_name(tl[0]) == tl[1]


class BondModelTest(APITransactionTestCase):
    def test_bond_model(self):
        for tb in test_bonds:
            test_model = Bond(**tb["exp_output"])
            assert test_model.isin == tb["exp_output"]["isin"]
            assert test_model.size == tb["exp_output"]["size"]
            assert test_model.currency == tb["exp_output"]["currency"]
            assert test_model.maturity == tb["exp_output"]["maturity"]
            assert test_model.lei == tb["exp_output"]["lei"]
            assert test_model.legal_name == tb["exp_output"]["legal_name"]

    def test_json_model(self):
        user = make_fake_user('testname', 'testpass')
        for tb in test_bonds:
            test_model = Bond(owner=user["user"],**tb["exp_output"])
            self.assertJSONEqual(test_model.json(),json.dumps(tb["exp_output"]))

    def test_store(self):
        user = make_fake_user('testname', 'testpass')
        for tb in test_bonds:
            tb = tb["exp_output"]
            test_model = Bond(owner=user["user"],**tb)
            test_model.save()
        test_db_records()


class PostGetTest(APITestCase):
    def test_post(self):
        self.post_bonds()
        test_db_records()

    def post_bonds(self):
        user = make_fake_user('testname', 'testpass')
        self.client.login(**user)
        print("Posting test bonds (May take a while)")
        for tb in test_bonds:
            resp = self.client.post("/bonds/", tb["input"], format='json')
            self.assertJSONEqual(resp.data, json.dumps(tb["exp_output"]))

    def test_get_all(self):
        self.post_bonds()
        resp = self.client.get("/bonds/", format="json")
        resp.render()
        results = json.loads(resp.content.decode('utf-8'))
        for i in range(len(results)):
            assert results[i] == test_bonds[i]["exp_output"]

    def test_single_clause(self):
        self.post_bonds()
        for key in test_bonds[0]["exp_output"].keys():
            for tb in test_bonds:
                resp = self.client.get(
                    "/bonds/?"+key+"="+str(tb["exp_output"][key]),
                    format="json"
                )
                resp.render()
                results = json.loads(resp.content.decode('utf-8'))
                assert tb["exp_output"] in results


class AuthTest(APITestCase):
    # Check for rejection when attempting to access bonds without login
    def test_reject_get(self):
        resp = self.client.get("/bonds/", format="json")
        resp.render()
        exp_msg = {"detail": "Authentication credentials were not provided."}
        assert json.loads(resp.content.decode('utf-8')) == exp_msg

    # Check for rejection when attempting to post bonds without login
    def test_reject_post(self):
        for tb in test_bonds:
            resp = self.client.post("/bonds/", tb["input"], format='json')
            resp.render()
            exp_msg = {"detail": "Authentication credentials were not provided."}
            assert json.loads(resp.content.decode('utf-8')) == exp_msg

    # Posts bonds as 2 separate users, checks if user can see all their and only
    # their bonds
    def test_access_control(self):
        user1 = make_fake_user("testuser1", "test12345")
        user2 = make_fake_user("testuser2", "test67890")
        # Post User 1 bonds
        user1_bonds = test_bonds[:len(test_bonds)//2]
        self.post_user_bonds(user1, user1_bonds)
        # Post User 2 bonds
        user2_bonds = test_bonds[len(test_bonds)//2:]
        self.post_user_bonds(user2, user2_bonds)
        # Get User 1 bonds, check if equal to original list
        self.check_user_bonds(user1, user1_bonds)
        # Get User 2 bonds, check if equal to original list
        self.check_user_bonds(user1, user1_bonds)

    # Login as user and post bonds
    def post_user_bonds(self, user, bonds):
        self.client.login(**user)
        print("Posting "+user["username"]+" bonds (May take a while)")
        for tb in bonds:
            resp = self.client.post("/bonds/", tb["input"], format='json')
            self.assertJSONEqual(resp.data, json.dumps(tb["exp_output"]))
        self.client.logout()

    # Login as user and compare posted bonds with originals
    def check_user_bonds(self, user, bonds):
        self.client.login(**user)
        resp = self.client.get("/bonds/", format="json")
        resp.render()
        results = json.loads(resp.content.decode('utf-8'))
        bonds_list = list()
        for b in bonds:
            assert b["exp_output"] in results
            bonds_list.append(b["exp_output"])
        for r in results:
            assert r in bonds_list
        self.client.logout()
