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
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.vector_store_action { VectorStoreAction }

node TypesenseVectorStoreAction :VectorStoreAction: {
    # Integrates with typesense vector database for retrieval augmented generation tasks

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);
    
    has host:str = os.environ.get('TYPESENSE_HOST','typesense'); # Use xxx.a1.typesense.net for Typesense Cloud
    has port:str = os.environ.get('TYPESENSE_PORT','8108'); # Use 443 for Typesense Cloud
    has protocol:str = os.environ.get('TYPESENSE_PROTOCOL','http'); # Use https for Typesense Cloud
    has api_key:str = os.environ.get('TYPESENSE_API_KEY','abcd');
    has api_key_name:str = "typesense_key";
    has connection_timeout:int = int(os.environ.get('TYPESENSE_CONNECTION_TIMEOUT_SECONDS','2'));
    has collection_name:str = "";
    
    can on_register() {

        # use agent_id if collection name not specified
        if(not self.collection_name) {
            self.collection_name = self.get_agent().id; 
        }

    }

    can on_enable() {

        # use agent_id if collection name not specified
        if(not self.collection_name) {
            self.collection_name = self.get_agent().id; 
        }

    }

    can get_client() {
        # """
        # Initializes and returns a Typesense client using configuration settings 
        # from environment variables.

        # Returns:
        #     typesense.Client: A configured Typesense client instance.
        
        # Raises:
        #     ValueError: If any required environment variable is not set.
        # """
        try {
            
            if not all([self.host, self.protocol, self.api_key, self.port, self.connection_timeout]) {
                raise ValueError("One or more required variables are missing.");
            }

            # Initialize and return the Typesense client
            return typesense.Client({
                'api_key': self.api_key,
                'nodes': [{
                    'host': self.host,
                    'port': self.port,
                    'protocol': self.protocol
                }],
                'connection_timeout_seconds': self.connection_timeout
            });

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can get_collection(collection_name:str) {
        # """
        # Returns a Typesense collection by name or None if it doesn't exist
        # """
        collection = None;

        try {
            if(client := self.get_client()) {
                collection = client.collections[collection_name];
                collection.retrieve();
            }
        } except typesense.exceptions.ObjectNotFound {
            return None;
        }

        return collection;
    }

    can get_vectorstore() {
        # """
        # Initializes and returns a Typesense vectorstore reference using client 

        # Returns:
        #     VectorStore: A Typesense vectorstore object.
        
        # Raises:
        #     ValueError: If any required environment variable is not set.
        # """
        try {
            
            embedding = self.get_embedding_model();
            
            if not embedding {
                raise ValueError("Embedding model not found.");
            }

            if not self.collection_name {
                raise ValueError("Collection name not set.");
            }
            
            # # set the openai api key for embeddings via langchain
            # os.environ["OPENAI_API_KEY"] = self.openai_api_key;
            # # set up the embedding resource and vectorstore
            # embedding = OpenAIEmbeddings();
            
            if(client := self.get_client()) {
                return Typesense(
                    typesense_client=client,
                    embedding=embedding,
                    typesense_collection_name=self.collection_name,
                    text_key="text",
                );
            }
            
        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can add_embeddings(knodes:list[Document], ) {

        importing_error_message = "";
        try {
            
            # Try to parse the content as JSON
            try {
                data = json.loads(knodes);
            } except json.JSONDecodeError as e {
                importing_error_message = f"Failed to import knode JSON, {e}";
            }

            # Try to parse the content as YAML
            try {
                data = yaml.safe_load(knodes);
            } except yaml.YAMLError as e {
                importing_error_message = f"Failed to import knode YAML, {e}";
            }


            if(client := self.get_client()) {
                for doc in data{
                    client.collections[self.collection_name].documents.create(doc);
                }
            }
            
            return True;
        } except Exception as e {
            self.logger.error(f"an exception occurred, {e}");
            self.logger.error(importing_error_message);
            return False;
        }
    }

    can create_key(description:str=['admin_key'], actions:list=['*'], collections:list=['*']) -> Dict {
        # """
        # Creates a new Typesense key.

        # :param client_config: Configurations for Typesense client instance
        # :param description: Description for the key
        # :param actions: List of actions allowed by the key
        # :param collections: List of collections the key is scoped to
        # :return: Response from the Typesense server
        # """

        try {

            if(client := self.get_client()) {
                # create key
                return client.keys.create({
                    "description": description, 
                    "actions": actions, 
                    "collections": collections
                });
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can retrieve_key(key_id:str) -> Dict {
        # """
        # Retrieves a key by its ID.

        # :param client_config: Configurations for Typesense client instance
        # :param key_id: ID of the key
        # :return: Key details
        # """
        try {

            if(client := self.get_client()) {
                # retrieve key
                return client.keys[key_id].retrieve();
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can delete_key(key_id:str) -> Dict {
        # """
        # Retrieves a key by its ID.

        # :param client_config: Configurations for Typesense client instance
        # :param key_id: ID of the key
        # :return: Key details
        # """
        try {
            
            if(client := self.get_client()) {
                # retrieve key
                return client.keys[key_id].delete();
            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return None;
    }

    can list_documents(page:int = 1, per_page:int = 10) -> dict {
        # """
        # lists all documents in the vectorstore.

        # :param page (int) – the current page.
        # :param per_page (int) – the maximum number of items per page
        # :param params (Dict) – Optional list of typesense params.
        
        # :returns List of documents with this structure 
        # {
        #     'page': 1,
        #     'per_page': 10,
        #     'total': 114,
        #     'documents': [ {id:'abc', 'metadata':{}, 'text':'xyz'} ]
        # }
        # """
        try {
            
            if(collection := self.get_collection(self.collection_name)) {
                
                # Fetch documents using the search endpoint with pagination
                results = collection.documents.search({
                    'q': '*',
                    'per_page': per_page,
                    'page': page,
                    'exclude_fields': 'vec'
                });

                # extract the document record
                documents = [];
                hits = results.get('hits', []);
                for item in hits {
                    documents.append(item.get('document'));
                }

                # Return paginated documents with their IDs
                return {
                    'page': page,
                    'per_page': per_page,
                    'total': results.get('found', 0),
                    'documents': documents
                }; 

            }

        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }

        return {
            'page': page,
            'per_page': per_page,
            'total': 0,
            'documents': []
        };
    }

    can get_document(id:str) -> dict {
        # """
        # Retrieves a document by its ID.

        # :param id: ID of the document 

        # :return: the document
        # """
        try {
            
            if(collection := self.get_collection(self.collection_name)) {
                # retrieve document
                if(document := collection.documents[id]) {
                    result = document.retrieve();
                    result.pop("vec", None);
                    return result;
                }

            }

        } except Exception as e {
            return None;
        }

    }

    can update_document(id:str, data:dict) -> dict {
        # """
        # Updates a document by its ID.

        # :param id: ID of the document to update
        # :param data: fields of the document to update, e.g. text, metadata

        # :return: the document
        # """
        try {
            
            if(collection := self.get_collection(self.collection_name)) {
                # update document
                if(document := collection.documents[id]) {
                    return document.update(data);
                }
                
            }

        } except Exception as e {
            return None;
        }

    }
    
    can delete_document(id:str) -> bool {
        # """
        # Deletes a document by its ID.

        # :param id: ID of the document to delete

        # :return: the deleted document
        # """
        try {
            
            if(collection := self.get_collection(self.collection_name)) {
                # delete document
                if(document := collection.documents[id]) {
                    return document.delete();
                }
            }

        } except Exception as e {
            return None;
        }

    }

    can delete_collection() -> bool {

        try {
            
            if(collection := self.get_collection(self.collection_name)) {
                # delete document
                return collection.delete();
            }

        } except Exception as e {
            return None;
        }

    }
}