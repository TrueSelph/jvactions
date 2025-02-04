import:jac from agent.core.agent { Agent }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }
import:py os;
import:py uuid;
import:py base64;

walker get_policy :interact_graph_walker: {
    can on_agent with Agent entry {
        self.agent_name = here.name;
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled == True)(?label == 'PolicyAction');
    }

    can on_action with Action entry {
        # replace {agent_name} with the agent's name
        content = here.content.replace("{agent_name}", self.agent_name);

        content_lines = content.splitlines();
        content = "";

        # remove trailing whitespace from each line
        for line in content_lines {
            line = line.lstrip();
            content += line + '\n';
        }

        self.response = content;
    }
}
