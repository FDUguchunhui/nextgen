from nextgen.agents.data_scientist_agent import get_vanna_instance
import os


# read data/train_data_scientist.jsonl
import json


# train the data scientist agent
vn = get_vanna_instance(model='openai', chroma_path='database/data_scientist_chroma', sql_path='database/nextgen.db')

with open('data/train_data_scientist.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        if data['type'] == 'question_sql':
            vn.train(question=data['question'], sql=data['sql'])
        elif data['type'] == 'documentation':
            vn.train(documentation=data['documentation'])

df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

for ddl in df_ddl['sql'].to_list():
  vn.train(ddl=ddl)

from vanna.flask import VannaFlaskApp
app = VannaFlaskApp(vn)
app.run()
