import:py json;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from actions.jivas.langchain_model_action.langchain_model_action { LangChainModelAction }
import:jac from jivas.agent.action.model_action { ModelAction, ModelActionResult }


node FunctionInteractAction :InteractAction: {
    # based on an utterance, classifies agaisnt registered intents

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has strict:bool = False; # if strict, only actions belonging to matched functions will be executed.
    has chained:bool = False; # if chained, only executes when one of its actions added by the intent interact action is queued.
    has history:bool = False;
    has history_size:int = 3;
    has max_statement_length:int = 500;
    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o-mini";
    has model_temperature:float = 0.2;
    has model_max_tokens:int = 2048;
    has exceptions:list = [];


    can touch(visitor: interact_graph_walker) -> bool {
        # authorize the interact to run

        if(self.chained and self.get_agent().get_actions().get(action_label="IntentInteractAction")) {
            function_index = self.get_function_index(visitor); 
            for intent in visitor.interaction_node.get_intents() {
                if intent in function_index.keys() and visitor.utterance {
                    return True;
                }
            }
        } elif visitor.utterance {
            return True; 
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {
        
        # load up all functions by interact actions
        function_index = self.get_function_index(visitor); 
        # get a consolidated list of functions for chat completions
        functions = [item for sublist in function_index.values() for item in sublist];
        
        if(function_index) {

            tools = self.process_functions(visitor, functions);
            
            for tool in tools {
                # remap the resulting function to the action it came from
                action_label = self.get_action_by_function(index = function_index, function_name = tool.get('name', None));
                visitor.interaction_node.add_function(action_label = action_label, function = tool);
            }
                       
        }

        return visitor.export();
    }

    can process_functions(visitor: interact_graph_walker, functions:list, kwargs:dict = {}) -> list {
        
        # Process keyword arguments to configure function behavior
        if "history" in kwargs {
            history = kwargs["history"];
        }else {
            history = self.history;
        }

        if "history_size" in kwargs {
            history_size = kwargs["history_size"];
        }else {
            history_size = self.history_size;
        }

        if "max_statement_length" in kwargs {
            max_statement_length = kwargs["max_statement_length"];
        }else {
            max_statement_length = self.max_statement_length;
        }

        if "model_action" in kwargs {
            model_action = kwargs["model_action"];
        }else {
            model_action = self.model_action;
        }

        if "model_name" in kwargs {
            model_name = kwargs["model_name"];
        }else {
            model_name = self.model_name;
        }

        if "model_temperature" in kwargs {
            model_temperature = kwargs["model_temperature"];
        }else {
            model_temperature = self.model_temperature;
        }

        if "model_max_tokens" in kwargs {
            model_max_tokens = kwargs["model_max_tokens"];
        }else {
            model_max_tokens = self.model_max_tokens;
        }



        prompt_messages = [];
        if (history) {
            # grab the history        
            statements = visitor.frame_node.get_transcript_statements(interactions = history_size, max_statement_length = max_statement_length);

            if (statements) {
                prompt_messages.extend(statements);
                self.logger.debug(f"history: {json.dumps(statements)}");
            }

            # prompt_messages.extend([{"human": visitor.utterance}]);
        } else {
            # here we cater to whether we have context information or not..
            prompt_messages = [
                {"human": visitor.utterance}
            ];
        }                                    
        
        if(model_action := self.get_agent().get_actions().get(action_label=model_action)) {
            
            if (model_action_result := model_action.call_model(
                prompt_messages = prompt_messages,
                prompt_variables = {},
                kwargs = {
                    "functions": functions,
                    "model_name": model_name,
                    "model_temperature": model_temperature,
                    "model_max_tokens": model_max_tokens
                },
                interaction_node = visitor.interaction_node
            )) {

                if(tools := model_action_result.get_result()) {
                    return tools;
                }
            }
        }

        return [];
    }

    can get_function_index(visitor: interact_graph_walker) -> dict {
        # retrieves a dictionary of anchor statements from each action for classification; to be spawned on an agent
        function_index = {};

        # get a list of all interact actions
        all_actions = self.get_agent().get_actions().get_all(filter_interact_actions=True, filter_enabled_actions=True);

        for action_node in all_actions {
            # only enabled actions which implement functions are of interest to us
            if(action_node.functions and action_node.label != self.get_type()) {
                function_index[action_node.label] = action_node.functions;
            }
        }

        return function_index;
    }

    can get_action_by_function(index:dict, function_name:str) {
        # searches function index and returns action by function name

        for (key, value) in index.items() {
            for function in value {
                if function_name == function.get('function', {}).get('name', None) {
                    return key;
                }
            }
        }

        return None;
    }

    can healthcheck() -> bool {
        try {
            if(self.model_action and self.model_name){
                return True;
            }
            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }

}