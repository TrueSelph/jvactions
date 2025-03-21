import:py os;
import:py json;
import:py yaml;
import:py schedule;
import:py logging;
import:py traceback;
import:py typesense;
import:py from langchain_community.vectorstores { Typesense }
import:py from langchain_openai { OpenAIEmbeddings }
import:py from langchain_core.vectorstores.base { VectorStore }
import:py from langchain_core.documents.base { Document }
import:py from logging { Logger }
import:jac from agent.action.action { Action }
import:jac from agent.action.vector_store_action { VectorStoreAction }

node DeepDocAction :VectorStoreAction: {
    # Integrates with typesense vector database for retrieval augmented generation tasks

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);
    
    has api_url:str = "http://localhost:5000/document/upload_and_chunk"; # api url
    has api_key:str = "";
    has headers:dict = {'Content-Type': 'application/json'};
}