import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.utils.utils import utils
import logging

logger = logging.getLogger(__name__)

class LLMModelProvider:
    """
    Provides LLM models based on the environment variables.
    """

    def __init__(self, model_name=None):
        """
        Initializes the LLMModelProvider.

        Args:
            model_name (str, optional): The name of the model to use. If None, it defaults 
                                       to the model specified in utils.py or detected from environment variable.
        """
        if model_name is None:
            self.model_name = os.getenv("LLM_MODEL_NAME", utils.model_name)
        else:
            self.model_name = model_name
        self.api_key_env_var = None

        self.llm = self._get_llm()
        

    def _get_llm(self):
        """
        Retrieves the appropriate LLM based on the environment variables.

        Returns:
            ChatGoogleGenerativeAI or ChatOpenAI: The configured LLM.

        Raises:
            ValueError: If the specified model name or API key is not recognized or found.
        """
        logger.info(f"loading model : {self.model_name}")
        if self.model_name.startswith("gemini"):
            self.api_key_env_var = "GOOGLE_API_KEY"
            if self.api_key_env_var not in os.environ:
                raise ValueError(
                    f"Environment variable '{self.api_key_env_var}' not set for Gemini model."
                )
            
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                google_api_key=os.environ[self.api_key_env_var]
            )
        elif self.model_name.startswith("gpt"):
            self.api_key_env_var = "OPENAI_API_KEY"
            if self.api_key_env_var not in os.environ:
                raise ValueError(
                    f"Environment variable '{self.api_key_env_var}' not set for GPT model."
                )
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=0,
                max_tokens=None,
                openai_api_key=os.environ[self.api_key_env_var]
            )
        else:
            raise ValueError(
                f"Unsupported model name: '{self.model_name}'. "
                "Supported models are 'gemini-*' and 'gpt-*'."
            )

    def get_model(self):
        """
        Returns the configured LLM model.

        Returns:
            ChatGoogleGenerativeAI or ChatOpenAI: The configured LLM.
        """
        return self.llm

    def get_model_name(self):
        """
        Returns the name of the configured LLM model.
        Returns:
          str: the name of the configured LLM Model
        """
        return self.model_name

llm_model_provider = LLMModelProvider()