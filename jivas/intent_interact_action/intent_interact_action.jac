import:py json;
import:py logging;
import:py traceback;
import:py from logging {Logger}
import:py from agent.modules.agentlib.utils {Utils}
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_action { InteractAction }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }
import:jac from agent.action.model_action { ModelAction, ModelActionResult }

node IntentInteractAction :InteractAction: {
    # based on an utterance, classifies agaisnt registered intents

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has strict:bool = True; # if strict, only actions belonging to matched functions will be executed.
    has prompt:str = "You are an intent classification model. Perform the following steps to determine the intent of MESSAGE with context from HISTORY. Do not provide explanations, only the final output:\n1. For each key-value mapping in ANCHOR_INDEX, examine the list of statements in value mapped to each key against the MESSAGE.\n2. Determine which list of statements best align with the intent of MESSAGE.\n3. If there are one or more confident alignments, return the corresponding key or keys in a comma-separated list, otherwise, return 'unclassified'. \n\nMESSAGE: \n{utterance}\n\nANCHOR_INDEX: \n{anchor_index}\n\nHISTORY: \n{history}";
    has history_size:int = 5;
    has max_statement_length:int = 500;
    has model_action:str = "LangChainModelAction";
    has model_name:str = "gpt-4o";
    has model_temperature:float = 0.2;
    has model_max_tokens:int = 2048;
    has exceptions:list = ['FunctionInteractAction']; # list of actions which are included in intent, regardless

    can touch(visitor: interact_graph_walker) -> bool {
        # authorize the interact to run
        if visitor.utterance {
            return True;
        }
    }

    can execute(visitor: interact_graph_walker) -> dict {

        # first, let's see if we have any defined anchors from any actions for classification
        anchor_index = self.get_anchor_index(visitor);

        if(anchor_index) {
            # grab the history
            history = visitor.frame_node.get_transcript(interactions = self.history_size, max_statement_length = self.max_statement_length, with_events = True);

            # prepare the prompt
            prompt_messages = [
                {"system": self.prompt}
            ];

            # set the prompt variables
            prompt_variables = {
                "anchor_index": Utils.escape_string(json.dumps(anchor_index)),
                "utterance": visitor.utterance,
                "history": history
            };

            result = None;

            if(model_action := self.get_agent().get_actions().get(action_label=self.model_action)) {

                if( model_action_result := model_action.call_model(
                    prompt_messages = prompt_messages,
                    prompt_variables = prompt_variables,
                    kwargs = {
                        "model_name": self.model_name,
                        "model_temperature": self.model_temperature,
                        "model_max_tokens": self.model_max_tokens
                    },
                    interaction_node = visitor.interaction_node
                )) {

                    if (result := model_action_result.get_result()) {
                        # add the resulting intent, if any to the interaction to trigger the relevant action(s)
                        intents = result.split(",");
                        # update the intents
                        for intent in intents {
                            visitor.interaction_node.add_intent(intent);
                        }
                    }

                }
            }
        }

        return visitor.export();
    }

    can get_anchor_index(visitor: interact_graph_walker) -> dict {
        # retrieves a dictionary of anchor statements from each action for classification; to be spawned on an agent
        anchor_index = {};

        # get a list of all interact actions
        all_actions = self.get_agent().get_actions().get_all(filter_interact_actions=True, filter_enabled_actions=True);

        for action_node in all_actions {
            # only actions which implement anchors are of interest to us
            if(action_node.anchors and action_node.label != self.get_type()) {
                anchor_index[action_node.label] = action_node.anchors;
            }
        }

        return anchor_index;
    }

}
