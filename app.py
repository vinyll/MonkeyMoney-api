from pathlib import Path
import json

from roll import Roll, HttpError
from roll.extensions import simple_server, cors

import models


app = Roll()
cors(app, origin="*", methods="*")


@app.route('/')
async def index(request, response):
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    template = Path(__file__).parent / 'index.html'
    with open(template, 'r') as f:
        response.body = f.read()


@app.route('/login', methods=['POST'])
async def login(request, response):
    import ipdb; ipdb.set_trace()
    email = request.json.get('email')
    password = request.json.get('password')
    user = models.get_user(email, password)
    response.body = json.dumps(user)


@app.route('/signup', methods=['POST'])
async def signup(request, response):
    email = request.json.get('email')
    password = request.json.get('password')
    user = models.create_user(email, password)
    response.body = json.dumps(user)


@app.route('/deposit', methods=['POST'])
async def post_deposit(request, response):
    sender_id = request.headers.get('AUTH')
    description = ''
    if not sender_id:
        raise HttpError(401, 'You must be authenticated')
    amount = int(request.json.get('amount'))
    if not 0 < amount <= 1000:
        raise Exception(f'Amount must be between 1 and 1000. It is {amount}.')
    transaction = models.deposit(sender_id, amount)
    response.body = json.dumps(transaction)


@app.route('/withdraw', methods=['POST'])
async def post_withdraw(request, response):
    transaction = get_transaction(id)
    if not transaction:
        raise Exception(f'No transaction matches {id}')
    sender = get_user(transaction[1])
    if not sender:
        raise Exception(f'No sender found for {transaction[1]}')
    amount = int(transaction[3])
    name = f'{sender[1]} {sender[2]}'

    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    template = Path(__file__).parent / 'transaction.html'
    with open(template, 'r') as f:
        response.body = f.read() \
          .replace('{amount}', str(amount)) \
          .replace('{user}', name) \
          .replace('{id}', id)

    raise Exception("models.withdraw view not implemented yet")


if __name__ == '__main__':
    simple_server(app)
