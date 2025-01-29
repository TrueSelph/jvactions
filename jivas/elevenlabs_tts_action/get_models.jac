import:jac from agent.core.agent { Agent }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }


walker get_models :interact_graph_walker: {

    has id:str = "";
    has response:list = [];

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='ElevenlabsTTSAction');
    }

    can on_action with Action entry {
        self.response = here.get_models();
    }

}