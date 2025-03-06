import:jac from jivas.agent.action.interact_action { InteractAction }


node IntroInteractAction :InteractAction: {
    # Dispatches an introductory prompt directive to persona_response_action if user is a first-time user.

    has prompt:str = "In a natural and brief manner: \n a. Introduce yourself by name and explain your role \n b. Refer the first-time user to read your AI policy at https://platform.trueselph.com/policy before continuing. It contains our privacy policy.";
    
    can touch(visitor: interact_graph_walker) -> bool {
        return visitor.interaction_node.is_new_user();
    }

    can execute(visitor: interact_graph_walker) -> dict {
        # add directive to issue introductory response
        visitor.interaction_node.add_directive(directive=self.prompt);
        return visitor.export();
    }
}
