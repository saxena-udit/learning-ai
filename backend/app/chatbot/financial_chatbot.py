from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from app.loader.financial_data_loader import financial_data_loader
from app.model.llm_models import llm_model_provider
from app.utils.utils import utils
from app.utils.logger import get_logger

# Get logger for this module
logger = get_logger("chatbot")


class FinancialChatbot:
    def __init__(self, model_name=None):
        if model_name is None:
            model_name = utils.model_name
        logger.info(f"Initializing FinancialChatbot with model: {model_name}")
        
        try:
            self.llm = llm_model_provider.get_model()
            self.json_output_parser = JsonOutputParser()
            self.output_parser = StrOutputParser()
            self.financial_data_loader = financial_data_loader
            logger.info("FinancialChatbot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing FinancialChatbot: {str(e)}", exc_info=True)
            raise

    def read_file(self, fileName):
        try:
            logger.debug(f"Reading file: {fileName}")
            with open(fileName, 'r') as file:
                content = file.read().strip()
            logger.debug(f"Successfully read file: {fileName}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {fileName}: {str(e)}", exc_info=True)
            raise

    def create_prompt_template(self, has_context):
        try:
            logger.debug(f"Creating prompt template with context: {has_context}")
            if has_context:
                system_prompt_template = self.read_file("app/templates/system_prompt_with_context.txt")
                logger.debug("Using system prompt with context")
            else:
                system_prompt_template = self.read_file("app/templates/system_prompt.txt")
                logger.debug("Using system prompt without context")

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt_template),
                    ("user", "Question:{question}"),
                ]
            )
            return prompt
        except Exception as e:
            logger.error(f"Error creating prompt template: {str(e)}", exc_info=True)
            raise

    def parser(self):
        return self.output_parser

    def retrieval_chain(self, has_context_user_input):
        try:
            logger.info(f"Creating retrieval chain with context: {has_context_user_input}")
            all_retrievers = self.financial_data_loader.vector_db_retriever()
            has_context = has_context_user_input and len(all_retrievers) > 0
            
            if has_context != has_context_user_input:
                logger.warning(f"Context availability mismatch: User requested {has_context_user_input}, actual {has_context}")
            
            prompt = self.create_prompt_template(has_context)

            if not has_context:
                logger.info("Using basic prompt without context")
                retrieval_chain = {
                    "question": lambda x: x["question"]
                } | prompt | self.llm | self.parser()
            else:
                logger.info(f"Using context-aware prompt with {len(all_retrievers)} vector databases")
                retrieval_chain = {
                    "question": lambda x: x["question"],
                    "context": lambda x: self.financial_data_loader.search_vector_db(x["question"])
                } | prompt | self.llm | self.parser()

            return retrieval_chain
        except Exception as e:
            logger.error(f"Error creating retrieval chain: {str(e)}", exc_info=True)
            raise 

financial_chatbot = FinancialChatbot()