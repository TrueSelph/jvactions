import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }


walker list_documents :interact_graph_walker: {

    has page:int = 1;
    has per_page:int = 10;
    has response:dict = {};

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='TypesenseVectorStoreAction');
    }

    can on_action with Action entry {
        self.response = here.list_documents(
            page=self.page,
            per_page=self.per_page
        );
        
    }

}