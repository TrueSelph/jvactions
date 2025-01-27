import:jac from agent.action.action { Action }

node AccessControlAction :Action: {
    # allows access control permissions to be defined per channel, action and session_id; maintains perm configs as a record of session_ids and associated role

    has exceptions:list = []; # collection of actions which are exempt from permissions

    has permissions:dict = {
        "default": { # channel
            "any":{ # resource, e.g. action type; 'any' is default
                "deny":[], # can accommodate specific session_ids or 'all'
                "allow":["all"] # can accommodate specific session_ids or 'all'
            }
        },
        "whatsapp": {
            "any":{
                "deny":[],
                "allow":["all"]
            }
        }

    };

    can has_action_access(session_id:str, action_label:str, channel:str="default") {
        # executes any attached and enabled whatsapp whitelist actions
        access = False;

        if(self.enabled) {
            # access permissions and determine access
            if(channel in self.permissions.keys()) {

                if(action_label in self.permissions[channel].keys()) {
                    if("allow" in self.permissions[channel][action_label].keys()) {
                        if(session_id in self.permissions[channel][action_label]["allow"] or "all" in self.permissions[channel][action_label]["allow"]) {
                             access = True;
                        }
                    }
                    if("deny" in self.permissions[channel][action_label].keys()) {
                        if(session_id in self.permissions[channel][action_label]["deny"] or "all" in self.permissions[channel][action_label]["deny"]) {
                            access = False;
                        }
                    }
                }


                if("any" in self.permissions[channel].keys()) {
                    if("allow" in self.permissions[channel]['any'].keys()) {
                        if("all" in self.permissions[channel]['any']["allow"] or session_id in self.permissions[channel]['any']["allow"]) {
                            access = True;
                        }
                    }
                    if("deny" in self.permissions[channel]['any'].keys()) {
                        if("all" in self.permissions[channel]['any']["deny"] or session_id in self.permissions[channel]['any']["deny"]) {
                            access = False;
                        }
                    }
                }
            }
        } else {
            access = True;
        }

        return access;

    }

}