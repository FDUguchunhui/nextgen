
import os
from langchain_openai import ChatOpenAI

# Instantiate the client. Make sure the client points to the self-hosted LLM.
def md_anderson_llm():
    return ChatOpenAI(
            api_key="unused",
            base_url="https://apimd.mdanderson.edu/dig/llm/llama31-70b/v1/",
            default_headers={"Ocp-Apim-Subscription-Key": os.environ["APIM_SUBSCRIPTION_KEY"]},
    )


# # Construct your messages. You can specify 'user', 'system', or 'assistant'
# # roles. You can also pass in a list of messages with different roles to
# # build the context in whatever way you'd like.
# chat = [{"role": "user", "content": "What is Deep Learning?"}]

# best_output = client.invoke(chat, stop=["."]).content
# print(best_output)

