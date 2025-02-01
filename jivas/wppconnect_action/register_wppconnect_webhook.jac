import:py logging;
import:py from logging { Logger }
import:py from agent.modules.agentlib.utils { Utils }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact { interact }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }
import:jac from agent.core.agent { Agent }
import:jac from agent.memory.frame { Frame }
import:jac from agent.memory.memory { Memory }
import:py from .modules.wppconnect_api { WppconnectAPI }

walker register_wppconnect_webhook :interact_graph_walker: {

    has response:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    obj __specs__ {
        # make this walker visible in API
        static has private: bool = False;
    }

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='WppconnectAction');
    }

    can on_action with Action entry {
        self.response = here.register_wppconnect_webhook();
    }

}