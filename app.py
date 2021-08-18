from os import environ as env
from roll import Roll
from roll.extensions import simple_server, cors

from models import RGraph
import routes


app = Roll()
cors(app, origin="*", methods="*", headers=["*", "Auth"])
db = RGraph(database=env.get("DB_NAME", "monkeymoney"))
routes.init(app, db)


if __name__ == '__main__':
    simple_server(app)
