from unittest import TestCase

import redis
from models import RGraph


db = RGraph(database="monkeymoney_test")


class ModelsTest(TestCase):
    def setUp(self):
        self.user = db.create_user('test@localhost', 'p4ssw0rd')
        self.friend = db.create_user('buddy@localhost', 'b499y', 40)

    def tearDown(self):
        db.destroy("I am deleting all data in monkeymoney_test")

    def test_create_and_get_user(self):
        self.assertEqual(self.user['email'], 'test@localhost')
        self.assertEqual(self.user['password'], 'p4ssw0rd')
        self.assertEqual(len(self.user['uid']), 36)
        self.assertEqual(self.user['credit'], 0)

    def test_get_user_by(self):
        self.assertEqual(db.get_user_by('email', 'non@existing'), None)
        self.assertDictEqual(db.get_user_by('email', 'test@localhost'), self.user)
        self.assertDictEqual(db.get_user_by('uid', self.user['uid']), self.user)

    def test_update_user_credit(self):
        self.assertEqual(self.user['credit'], 0)
        db.update_user_credit(self.user['uid'], 3)
        updated = db.get_user_by('uid', self.user['uid'])
        self.assertEqual(updated['credit'], 3)

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
        withdrawal = db.withdraw(deposit['uid'], recipient['uid'])
        self.assertEqual(withdrawal['edge']['uid'], deposit['uid'])
        transaction = db.get_transaction(deposit['uid'])
        self.assertEqual(transaction['origin']['uid'], self.user['uid'])
        self.assertEqual(transaction['destination']['uid'], recipient['uid'])
        self.assertEqual(transaction['edge']['amount'], 13)


    def test_get_user_transactions(self):
        deposits = [
            db.deposit(self.friend['uid'], 20),
            db.deposit(self.user['uid'], 8),
            db.deposit(self.user['uid'], 5),
        ]
        withdrawals = [
            db.withdraw(deposits[0]['uid'], self.user['uid']),
            db.withdraw(deposits[1]['uid'], self.friend['uid']),
            db.withdraw(deposits[2]['uid'], self.friend['uid']),
        ]
        transactions = db.get_user_transactions(self.user['uid'])
        self.assertEqual(len(transactions), 3)
        self.assertEqual(transactions[2]['origin']['uid'], self.friend['uid'])
        self.assertEqual(transactions[2]['dest']['uid'], self.user['uid'])
        self.assertEqual(transactions[2]['edge']['amount'], 20)
