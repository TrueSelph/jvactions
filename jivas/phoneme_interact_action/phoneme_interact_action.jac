import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.interact_action { InteractAction }
import:py from .modules.phoneme_utils { PhonemeUtils }


node PhonemeInteractAction :InteractAction: {
    # manages phoneme-based prompting to customize the pronunciation of certain words for text-to-speech models used by an agent
    # always ensure that this is registered after the final response is generated

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has language:str = "en";
    has phonemes:dict = {}; # a key-value set of words and their corresponding phonetic representation in IPA, CMU or plain text

    can post_register() {
        # to ensure compatibility, add this action to the exception list in intent_classifier
        
        if(intent_interact_action_node := self.get_agent().get_actions().get(action_label='IntentInteractAction')) {
            if(self.get_type() not in intent_interact_action_node.exceptions) {
                intent_interact_action_node.exceptions += [self.get_type()];
            }
        }
        
    }

    can touch(visitor: interact_graph_walker) -> bool {
        if(visitor.interaction_node.has_response() and visitor.tts) {
            return True;
        } 
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # must run last.. look for the message and add the phoneme_message key to the interaction
        # go through the message and replace phonemes        
        phoneme_content = PhonemeUtils.phonetic_format(visitor.interaction_node.get_message().get_content(), self.phonemes);
        
        if(phoneme_content) {
            message = visitor.interaction_node.get_message();
            message.set_meta('phoneme_content', phoneme_content);
            visitor.interaction_node.set_message(message);
        } 

        return visitor.export();
    }


    can healthcheck() -> bool {
        try {
            if(self.language){
                return True;
            }
            return False;
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }
}
