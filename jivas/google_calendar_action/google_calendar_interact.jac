import:py logging;
import:py re;
import:py from logging { Logger }
import:py from jivas.agent.modules.agentlib.utils { Utils }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.interact { interact }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.memory.frame { Frame }
import:jac from jivas.agent.memory.memory { Memory }
import:py from modules.google_calendar_api { GoogleCalendarAPI }


walker google_calendar_interact :interact_graph_walker: {
    # called via a webhook whenever there are verification requests or inbound messages 
    # when activated, it will trigger the facebook interact action to communicate

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has headers:dict = {};
    # main param for incoming webhook data
    has params:dict = {};
    # main param for outgoing webhook data
    has response:dict = {};

    can on_agent with Agent entry {

        # when the webhook triggered update last_modified_timestamp in GoogleCalendarAction
        if( action_node:=(here.get_actions().get(action_label='GoogleCalendarAction')) ) {
            action_node.validate_request(self.headers);
        }
    }
}