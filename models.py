import json
from datetime import datetime
import redis
from redisgraph import Node, Edge, Graph, Path
from uuid import uuid4

r = redis.Redis(host='localhost', port=6379)
graph = Graph('monkeymoney', r)


def clean_str(string: str) -> str:
  return string.strip().lower()


def get_user_by_uid(uid: str) -> dict:
  uid = clean_str(uid)
  result = graph.query(f"""
    MATCH (u:User)
      WHERE u.uid = "{uid}"
    RETURN u
  """)
  if result.result_set:
    return result.result_set[0][0].properties


def get_user(email: str, password: str) -> dict:
  email = clean_str(email)
  result = graph.query(f"""
    MATCH (u:User)
      WHERE u.email = "{email}" AND u.password = "{password}"
    RETURN u
  """)
  if result.result_set:
    return result.result_set[0][0].properties


def create_user(email: str, password: str, credit: int=0) -> None:
  email = clean_str(email)
  if get_user(email, password):
    raise Exception(f"A user with email '{email}' already exists.")

  uid = str(uuid4())
  now = int(datetime.now().timestamp())

  graph.add_node(Node(label='User', properties = {
    'email': email,
    'password': password,
    'uid': uid,
    'datetime': now,
    'credit': credit,
  }))
  graph.flush()
  return get_user_by_uid(uid)


def deposit(src_id, amount):
  now = int(datetime.now().timestamp())
  uid = str(uuid4())
  query = """
    MATCH (src:User) WHERE src.uid = "{src_id}"
    MERGE (n:Nobody)
    WITH src, n
    CREATE (src)-[t:Transaction {{amount: {amount}, datetime: {now}, uid: "{uid}"}}]->(n)
    RETURN t
  """.format(now=now, uid=uid, src_id=src_id, amount=amount)
  result = graph.query(query)
  if result.result_set:
    return result.result_set[0][0].properties


def withdraw(transaction_uid, dest_id):
  data = graph.query(f"""
    MATCH (src:User)-[t:Transaction]->(:Nobody) WHERE t.uid = "{transaction_uid}" RETURN src, t
  """)

  return graph.query(f"""
    MATCH (src:User)-[t:Transaction]->(:Nobody) WHERE t.uid = "{transaction_uid}"
    MATCH (dest:User) WHERE id(dest) = {dest_id}
    WITH src, t, dest, {{ amount: t.amount, datetime: t.datetime, uid: t.uid }} AS props
      CREATE (src)-[t_new:Transaction]->(dest)
      DELETE t
      SET t_new = props
    RETURN *
  """)
