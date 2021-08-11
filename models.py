import json
from datetime import datetime
from dataclasses import dataclass

import redis
from redisgraph import Node, Edge, Graph, Path
from uuid import uuid4


@dataclass
class Path(dict):
    origin: dict
    edge: dict
    destination: dict

def clean_str(string: str) -> str:
    return string.strip().lower()


class RGraph:
    def __init__(self, host='localhost', port=6379, database='monkeymoney'):
        r = redis.Redis(host=host, port=port)
        self.db = Graph(database, r)

    def get_user_by_uid(self, uid: str) -> dict:
        uid = clean_str(uid)
        result = self.db.query(f"""
          MATCH (u:User)
            WHERE u.uid = "{uid}"
          RETURN u
        """)
        if result.result_set:
            return result.result_set[0][0].properties

    def get_user(self, email: str, password: str) -> dict:
      email = clean_str(email)
      result = self.db.query(f"""
        MATCH (u:User)
          WHERE u.email = "{email}" AND u.password = "{password}"
        RETURN u
      """)
      if result.result_set:
        return result.result_set[0][0].properties

    def create_user(self, email: str, password: str, credit: int=0) -> dict:
      email = clean_str(email)
      if self.get_user(email, password):
        raise Exception(f"A user with email '{email}' already exists.")

      uid = str(uuid4())
      now = int(datetime.now().timestamp())

      self.db.add_node(Node(label='User', properties = {
        'email': email,
        'password': password,
        'uid': uid,
        'datetime': now,
        'credit': credit,
      }))
      self.db.flush()
      return self.get_user_by_uid(uid)

    def deposit(self, src_uid: str, amount: int) -> dict:
      now = int(datetime.now().timestamp())
      uid = str(uuid4())
      query = """
        MATCH (src:User) WHERE src.uid = "{src_uid}"
        MERGE (n:Nobody)
        WITH src, n
        CREATE (src)-[t:Transaction {{amount: {amount}, datetime: {now}, uid: "{uid}"}}]->(n)
        RETURN t
      """.format(now=now, uid=uid, src_uid=src_uid, amount=amount)
      result = self.db.query(query)
      if result.result_set:
        return result.result_set[0][0].properties

    def get_transaction(self, uid: str) -> Path:
      result = self.db.query(f"""
        MATCH (src:User)-[t:Transaction]->(dest)
          WHERE t.uid = "{uid}"
        RETURN src, t, dest
      """)
      if result.result_set:
        return {
          "origin": result.result_set[0][0].properties,
          "edge": result.result_set[0][1].properties,
          "destination": result.result_set[0][2].properties,
        }

    def get_transaction_by_code(self, code: str) -> Path:
      result = self.db.query(f"""
        MATCH (src:User)-[t:Transaction]->(dest)
          WHERE t.uid CONTAINS "-{code}-"
        RETURN src, t, dest
      """)
      if result.result_set:
        return {
          "origin": result.result_set[0][0].properties,
          "edge": result.result_set[0][1].properties,
          "destination": result.result_set[0][2].properties,
        }

    def withdraw(self, transaction_code: str, dest_uid: str) -> dict:
      result = self.db.query(f"""
        MATCH (src:User)-[t:Transaction]->(:Nobody) WHERE t.uid CONTAINS "-{transaction_code}-"
        MATCH (dest:User) WHERE dest.uid = "{dest_uid}"
        WITH src, t, dest, {{ amount: t.amount, datetime: t.datetime, uid: t.uid }} AS props
          CREATE (src)-[t_new:Transaction]->(dest)
          DELETE t
          SET t_new = props
        RETURN src, t_new, dest
      """)
      return {
        "origin": result.result_set[0][0].properties,
        "edge": result.result_set[0][1].properties,
        "destination": result.result_set[0][2].properties,
      }

    def destroy(self, *args) -> None:
      if not args or args[0] != "I know what I'm doing":
        raise Exception("Are you aware you are destroying all data?")
      self.db.query("""
        MATCH (a) DELETE a
      """)
