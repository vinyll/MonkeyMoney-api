from unittest import TestCase

import redis
from models import RGraph


db = RGraph(database="monkeymoney_test")


class ModelsTest(TestCase):
    def setUp(self):
        db.destroy("I know what I'm doing")
        db.create_user('test@localhost', 'p4ssw0rd')
        self.user = db.get_user('test@localhost', 'p4ssw0rd')

    def tearDown(self):
        db.destroy("I know what I'm doing")

    def test_create_and_get_user(self):
        self.assertEqual(self.user['email'], 'test@localhost')
        self.assertEqual(self.user['password'], 'p4ssw0rd')
        self.assertEqual(len(self.user['uid']), 36)
        self.assertEqual(self.user['credit'], 0)

    def test_deposit(self):
        deposit = db.deposit(self.user['uid'], 11)
        self.assertEqual(deposit['amount'], 11)
        self.assertEqual(len(deposit['uid']), 36)

    def test_get_transaction(self):
        deposit = db.deposit(self.user['uid'], 12)
        transaction: db.Path = db.get_transaction(deposit['uid'])
        self.assertEqual(len(transaction['edge']['uid']), 36)

    def test_get_transaction_by_code(self):
        deposit = db.deposit(self.user['uid'], 14)
        transaction: db.Path = db.get_transaction_by_code(deposit['uid'].split('-')[1])
        self.assertEqual(len(transaction['edge']['uid']), 36)

    def test_withdraw(self):
        recipient = db.create_user('igot@paid', 'pa1d')
        deposit = db.deposit(self.user['uid'], 13)
        db.withdraw(deposit['uid'].split('-')[1], recipient['uid'])
        transaction = db.get_transaction(deposit['uid'])
        self.assertEqual(transaction['origin']['uid'], self.user['uid'])
        self.assertEqual(transaction['destination']['uid'], recipient['uid'])
        self.assertEqual(transaction['edge']['amount'], 13)
