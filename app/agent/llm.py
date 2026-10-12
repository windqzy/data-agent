from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# llm = init_chat_model(
#     model=app_config.llm.model_name,
#     model_provider='openai',
#     base_url='',
#     api_key=app_config.llm.api_key,
#     temperature=0
# )

llm = init_chat_model(
    model=app_config.llm.model_name,
    model_provider="ollama",
    base_url="http://localhost:11434",
    temperature=0
)

if __name__ == "__main__":
    result = llm.invoke("你是谁")
    print(result.content)
