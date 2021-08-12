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
        response.body = json.dumps(user)

    @app.route('/profile/<uid>')
    async def get_profile(request, response, uid):
        user = db.get_user_by('uid', uid)
        if not user:
            raise HttpError(404)
        response.body = json.dumps(user)

    @app.route('/deposit', methods=['POST'])
    async def post_deposit(request, response):
        sender_id = request.headers.get('AUTH')
        if not sender_id:
            raise HttpError(401, 'You must be authenticated')
        amount = int(request.json.get('amount'))
        if not 0 < amount <= 1000:
            raise Exception(f'Amount must be between 1 and 1000. It is {amount}.')
        transaction = db.deposit(sender_id, amount)
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
            raise HttpError(400, "The transaction is not valid")
        # Enough credit
        if trans['edge']['amount'] > trans['origin']['credit']:
            raise HttpError(400, "The amount exceeds the sender's credit")
        # Assign transaction to user
        withdrawal = db.withdraw(trans['edge']['uid'], recipient_uid)
        # Credit out giver
        db.update_user_credit(withdrawal['origin']['uid'], withdrawal['origin']['credit'] - withdrawal['edge']['amount'])
        db.update_user_credit(withdrawal['destination']['uid'], withdrawal['destination']['credit'] + withdrawal['edge']['amount'])
        response.body = json.dumps(withdrawal)