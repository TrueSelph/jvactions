import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from agent.core.agent { Agent }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }


walker import_knodes :interact_graph_walker: {
    has data:str = "";
    has response:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='TypesenseVectorStoreAction');
    }

    can on_action with Action entry {
        self.response = here.import_knodes(self.data);
    }

}