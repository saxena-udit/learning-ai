from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from loader.financial_data_loader import FinancialDataLoader
from utils import model_name
import logging

logger = logging.getLogger(__name__)


class LangchainGeminiChatbot:
    def __init__(self, model_name=model_name):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            # other params...
        )
        self.json_output_parser = JsonOutputParser()
        self.output_parser = StrOutputParser()
        self.financial_data_loader = FinancialDataLoader()

    def read_file(self, fileName):
        with open(fileName, 'r') as file:
            return file.read().strip()

    def create_prompt_template(self, has_context):
        if has_context:
            system_prompt_template = self.read_file("templates/system_prompt_with_context.txt")
        else:
            system_prompt_template = self.read_file("templates/system_prompt.txt")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_template),
                ("user", "Question:{question}"),
            ]
        )
        return prompt

    def parser(self):
        return self.output_parser

    def retrieval_chain(self, has_context_user_input):
        all_retrievers = self.financial_data_loader.vector_db_retriever()
        has_context = has_context_user_input and len(all_retrievers) > 0
        prompt = self.create_prompt_template(has_context)

        if not has_context:
            logger.info("Using PDF chunks as a context")
            retrieval_chain = {
                "question": lambda x: x["question"]
            } | prompt | self.llm | self.parser()
        else:
            logger.info(f"Loaded {len(all_retrievers)} vector databases.")
            retrieval_chain = {
                "question": lambda x: x["question"],
                "context": lambda x: self.financial_data_loader.search_vector_db(x["question"])
            } | prompt | self.llm | self.parser()

        return retrieval_chain

