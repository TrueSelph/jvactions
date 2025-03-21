import:py logging;
import:py os;
import:py traceback;
import:py sys;
import:py json;
import:py requests;
import:py from logging { Logger }
import:py from PIL { Image }
import:jac from agent.core.agent { Agent }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }
import:py from .modules.upload_and_chunk { UploadAndChunk }


walker parse_pdfs :interact_graph_walker: {
    has data:list = [];
    has files:list = [];
    has urls:list = [];
    has response:bool = False;
    has embeddings:bool = False;
    has deepdoc_action:str = "DeepDocAction";

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='TypesenseVectorStoreAction');
    }

    can on_action with Action entry {
        # grab urls and see if its enabled
        if(self.urls){
            # iterate over urls and process
            for url in self.urls{
                # process pdf
                response = UploadAndChunk.upload_and_chunk([url]);

                if(response){
                    if(self.embeddings){
                        # import with embeddings
                        self.response = here.add_embeddings(json.dumps(response));
                    }else{
                        # import without embeddings
                        self.response = here.import_knodes(json.dumps(response));
                    }
                } else {
                    # set response
                    self.response = response.text;
                }
            }
        } else {
            self.response = "No urls provided";
        }
    }
}