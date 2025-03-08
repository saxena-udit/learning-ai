from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI

from loader.financial_data_loader import vector_db_retriever, search_vector_db
from utils import model_name


import logging

logger = logging.getLogger(__name__)



def read_file(fileName):
    with open(fileName, 'r') as file:
        return file.read().strip()
    
## Prompt Template with conditional context
def create_prompt_template(has_context):
    if has_context:
        system_prompt_template = read_file("templates/system_prompt_with_context.txt")  

    else:
        system_prompt_template = read_file("templates/system_prompt.txt")
        

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_template),
            ("user", "Question:{question}"),
        ]
    )
    return prompt


# ollama LLAma2 LLm 
llm= ChatGoogleGenerativeAI(
    model=model_name,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

json_output_parser = JsonOutputParser()
output_parser = StrOutputParser()

def parser():
    return output_parser

# Adding context to the chain.
def retrieval_chain(has_context_user_input):
    # Adding context to the chain.
    all_retrievers = vector_db_retriever()
    has_context = has_context_user_input and len(all_retrievers)>0
    prompt = create_prompt_template(has_context)
    if not has_context:
        logger.info("Using PDF chunks as a context")        
        retrieval_chain = {
            "question": lambda x: x["question"]
        } | prompt | llm | parser()
    else:
        logger.info(f"Loaded {len(all_retrievers)} vector databases.")
            
        # Create a chain that retrieves from multiple vector databases
        
        retrieval_chain = {
            "question": lambda x: x["question"],
            "context": lambda x: search_vector_db(x["question"])
        } | prompt | llm | parser()
        
    return retrieval_chain
    
