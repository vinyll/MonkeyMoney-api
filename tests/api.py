from unittest import TestCase
import json

import requests
from roll import Roll
from models import RGraph
import routes

# Server is run aside
# Database name should therefore be set as en environment variable
# from the server script
app = Roll()
db = RGraph(database="monkeymoney_test")
routes.init(app, db)


def url(uri):
    return f"http://127.0.0.1:3579{uri}"


class ApiTest(TestCase):
    def setUp(self):
        self.user = db.create_user('test@local', 't3st', 10)

    def tearDown(self):
        db.destroy("I am deleting all data in monkeymoney_test")

    def test_get_profile_error(self):
        response = requests.get(url('/profile/123'))
        self.assertEqual(response.status_code, 404)

    def test_get_profile(self):
        response = requests.get(url(f"/profile/{self.user['uid']}"))
        self.assertEqual(response.status_code, 404)

    def test_login_error(self):
        response = requests.post(url('/login'), data=json.dumps({
            'email': 'dummy@local',
            'password': 'dummy'
        }))
        self.assertEqual(response.status_code, 403)

    def test_login(self):
        response = requests.post(url('/login'), data=json.dumps({
            'email': f'test@local',
            'password': 't3st'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['credit'], self.user['credit'])
        self.assertEqual(len(response.json()['uid']), 36)

    def test_signup_duplicate(self):
        response = requests.post(url('/signup'), data=json.dumps({
            'email': self.user['email'],
            'password': 't4st'
        }))
        self.assertEqual(response.status_code, 400)

    def test_signup(self):
        response = requests.post(url('/signup'), data=json.dumps({
            'email': f'test2@local',
            'password': 't4st'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['uid']), 36)

    def test_me(self):
        response = requests.get(url('/me'), headers={'AUTH': self.user['uid']})
        self.assertEqual(response.status_code, 200)
        user = response.json()
        self.assertNotIn('password', user.keys())
        self.assertEqual(user['uid'], self.user['uid'])
        self.assertEqual(user['email'], self.user['email'])

    def test_transaction(self):
        deposit = db.deposit(self.user['uid'], 11)
        code = deposit['uid'].split('-')[1]
        response = requests.get(url(f'/transaction/{code}'), headers={'AUTH': self.user['uid']})
        self.assertEqual(response.status_code, 200)
        transaction = response.json()
        self.assertEqual(transaction['edge']['uid'], deposit['uid'])
        self.assertEqual(transaction['edge']['amount'], deposit['amount'])

    def test_withdrawal(self):
        deposit = db.deposit(self.user['uid'], 8)
        buddy = db.create_user('buddy@local', 'bu99y', 20)
        response = requests.post(url('/withdraw'), data=json.dumps({
            'code': deposit['uid'].split('-')[1],
        }), headers={'AUTH': buddy['uid']})
        self.assertEqual(response.status_code, 200)
        withdrawal = response.json()
        self.assertEqual(withdrawal['edge']['uid'], deposit['uid'])
        self.assertEqual(withdrawal['edge']['amount'], 8)
        me = db.get_user_by('uid', self.user['uid'])
        friend = db.get_user_by('uid', buddy['uid'])
        self.assertEqual(me['credit'], 2)
        self.assertEqual(friend['credit'], 28)


    def test_withdrawal_insuficent_credit(self):
        deposit = db.deposit(self.user['uid'], 8)
        buddy = db.create_user('buddy@local', 'bu99y', 20)
        response = requests.post(url('/withdraw'), data=json.dumps({
            'code': deposit['uid'].split('-')[1],
        }), headers={'AUTH': buddy['uid']})
        self.assertEqual(response.status_code, 200)
        withdrawal = response.json()
        self.assertEqual(withdrawal['edge']['uid'], deposit['uid'])
        self.assertEqual(withdrawal['edge']['amount'], 8)
        me = db.get_user_by('uid', self.user['uid'])
        friend = db.get_user_by('uid', buddy['uid'])
        self.assertEqual(me['credit'], 10 - 8)
        self.assertEqual(friend['credit'], 20 + 8)

    def test_withdrawal_multiple(self):
        deposit = db.deposit(self.user['uid'], 7)
        deposit2 = db.deposit(self.user['uid'], 9)
        buddy = db.create_user('buddy@local', 'bu99y', 0)
        requests.post(url('/withdraw'), data=json.dumps({
            'code': deposit['uid'].split('-')[1],
        }), headers={'AUTH': buddy['uid']})
        response = requests.post(url('/withdraw'), data=json.dumps({
            'code': deposit2['uid'].split('-')[1],
        }), headers={'AUTH': buddy['uid']})
        self.assertEqual(response.status_code, 401, "Not enough credit for 2nd withdrawal")
        me = db.get_user_by('uid', self.user['uid'])
        friend = db.get_user_by('uid', buddy['uid'])
        self.assertEqual(me['credit'], 10 - 7)
        self.assertEqual(friend['credit'], 7)
