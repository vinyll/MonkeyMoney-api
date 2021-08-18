import json

from roll import HttpError
from models import DuplicateError


def init(app, db):

    @app.route('/login', methods=['POST'])
    async def login(request, response):
        email = request.json.get('email')
        password = request.json.get('password')
        user = db.get_user(email, password)
        if not user:
            raise HttpError(403, "Please check your email and password")
        response.body = json.dumps(user)

    @app.route('/signup', methods=['POST'])
    async def signup(request, response):
        email = request.json.get('email')
        password = request.json.get('password')
        try:
            user = db.create_user(email, password)
        except DuplicateError as e:
            raise HttpError(400, str(e))
        response.status = 200
        response.body = json.dumps(user)

    @app.route('/profile/<uid>')
    async def get_profile(request, response, uid):
        user = db.get_user_by('uid', uid)
        if not user:
            raise HttpError(404)
        response.body = json.dumps(user)

    @app.route('/me')
    async def get_me(request, response):
        # Auth
        sender_uid = request.headers.get('AUTH')
        if not sender_uid:
            raise HttpError(401, 'You must be authenticated')
        user = db.get_user_by('uid', sender_uid)
        if not user:
            raise HttpError(404)
        del user['password']
        user['transactions'] = db.get_user_transactions(user['uid'])
        response.body = json.dumps(user)

    @app.route('/deposit', methods=['POST'])
    async def post_deposit(request, response):
        # Auth
        sender_uid = request.headers.get('AUTH')
        if not sender_uid:
            raise HttpError(401, 'You must be authenticated')
        # Amount range
        amount = int(request.json.get('amount'))
        if not 0 < amount <= 1000:
            raise Exception(f'Amount must be between 1 and 1000. It is {amount}.')
        # Sender credit
        user = db.get_user_by('uid', sender_uid)
        if amount > user['credit']:
            raise HttpError(401, "You don't have enough credit")
        transaction = db.deposit(sender_uid, amount)
        response.body = json.dumps(transaction)

    @app.route('/deposit', methods=['DELETE'])
    async def delete_deposit(request, response):
        sender_uid = request.headers.get('AUTH')
        if not sender_uid:
            raise HttpError(401, 'You must be authenticated')
        uid = int(request.json.get('uid'))
        transaction = db.get_transaction(uid)
        response.body = json.dumps(transaction)

    @app.route('/withdraw', methods=['POST'])
    async def post_withdraw(request, response):
        # Auth requireds
        recipient_uid = request.headers.get('AUTH')
        if not recipient_uid:
            raise HttpError(401, 'You must be authenticated')
        # Code must be valid
        code = request.json.get('code')
        trans: db.GraphPath = db.get_transaction_by_code(code)
        if not trans:
            raise HttpError(400, f'No transaction match {code}')
        # Transaction must not be assigned
        if trans['destination']:
            raise HttpError(401, "The transaction is not valid")
        # Enough credit
        if trans['edge']['amount'] > trans['origin']['credit']:
            raise HttpError(401, "The amount exceeds the sender's credit")
        # Assign transaction to user
        withdrawal = db.withdraw(trans['edge']['uid'], recipient_uid)
        # Credit out giver
        db.update_user_credit(withdrawal['origin']['uid'], withdrawal['origin']['credit'] - withdrawal['edge']['amount'])
        db.update_user_credit(withdrawal['destination']['uid'], withdrawal['destination']['credit'] + withdrawal['edge']['amount'])
        response.body = json.dumps(withdrawal)
