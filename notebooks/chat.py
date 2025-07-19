import vanna
from vanna.remote import VannaDefault
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
import dotenv
import os
import gradio as gr
dotenv.load_dotenv()


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={'api_key': OPENAI_API_KEY,
                      'model': 'gpt-4o-mini',
                      'path': './notebooks'})

vn.connect_to_sqlite('test.db')

from vanna.flask import VannaFlaskApp
app = VannaFlaskApp(vn)
app.run()
