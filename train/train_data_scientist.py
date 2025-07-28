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

# df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")

df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'ai_test'")

# This will break up the information schema into bite-sized chunks that can be referenced by the LLM
plan = vn.get_training_plan_generic(df_information_schema)
plan

# If you like the plan, then uncomment this and run it to train
vn.train(plan=plan)

# for ddl in df_ddl['sql'].to_list():
#   vn.train(ddl=ddl)

from vanna.flask import VannaFlaskApp
app = VannaFlaskApp(vn)
app.run()
