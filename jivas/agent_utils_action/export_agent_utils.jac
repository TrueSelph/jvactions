import:py json;
import:py yaml;
import:py from jivas.agent.modules.agentlib.utils { LongStringDumper }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.core.agent { Agent }

walker export_agent_utils :interact_graph_walker: {
    # accepts agent_id and returns dict of exported agent descriptor
    
    has daf_archive: bool = True;
    has export_json: bool = True;
    has knode_embeddings: bool = False;
    has knode_id: bool = False;
    has response:dict = {};

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = True; 
    }

    can on_agent with Agent entry {

        if(self.daf_archive) {

            # get descriptor 
            daf_descriptor = here.export_descriptor();
            
            # get daf info 
            daf_info = {
                "package": {
                    "name": daf_descriptor['meta']['namespace'],
                    "author": daf_descriptor['meta']['author'],
                    "version": daf_descriptor['meta']['version'],
                    "meta": {
                        "title": daf_descriptor['name'],
                        "description": daf_descriptor['description'],
                        "type": "daf"
                    },
                    "dependencies": daf_descriptor['meta']['dependencies']
                }
            };
            
            # get memory 
            daf_memory = here.get_memory().export_memory(agent_id=self.agent_id, session_id="", json=True, save_to_file=False)['memory'];
            
            # get knowledge
            daf_knowledge = [];
            if(vector_store_action := here.get_actions().get(action_label = "TypesenseVectorStoreAction")){
                daf_knowledge = json.loads(vector_store_action.export_knodes(export_json=True, embeddings=self.knode_embeddings, include_id=self.knode_id));
            }


            data = {
                "descriptor": daf_descriptor,
                "memory": daf_memory,
                "knowledge": daf_knowledge,
                "info": daf_info
            };

        }else {
            data = here.export_descriptor();
        }

        if(self.export_json) {
            self.response = data;
        }else {
            self.response = yaml.dump(data, Dumper=LongStringDumper, sort_keys=False);
        }
        return self.response;
    }
}