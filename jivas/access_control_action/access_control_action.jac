import:py traceback;
import:jac from jivas.agent.action.action { Action }

node AccessControlAction :Action: {
    # allows access control permissions to be defined per channel, action and session_id; maintains perm configs as a record of session_ids and associated role
    
    has exceptions:list = []; # collection of actions which are exempt from permissions

    has permissions:dict = {
        "default": { # channel
            "any":{ # resource, e.g. action type; 'any' is default
                "deny":[], # can accommodate specific session ids, session group name or 'all'
                "allow":["all"] # can accommodate specific session ids, session group name or 'all' 
            }
        },
        "whatsapp": {
            "any":{
                "deny":[],
                "allow":["all"]
            }
        }

    };

    has session_groups:dict = {}; # contains group name as key and list of session_ids as the value

    can add_session_group(group_name:str, session_ids:list) {
        # adds a session group to the session_groups dict
        self.session_groups[group_name] = session_ids;
    }

    can add_permission(channel:str, action_label:str, allow:list=[], deny:list=[]) {
        # adds a permission to the permissions dict
        if(channel not in self.permissions.keys()) {
            self.permissions[channel] = {};
        }
        if(action_label not in self.permissions[channel].keys()) {
            self.permissions[channel][action_label] = {"allow": [], "deny": []};
        }
        self.permissions[channel][action_label]["allow"] = list(set(self.permissions[channel][action_label]["allow"]).union(set(allow)));
        self.permissions[channel][action_label]["deny"] = list(set(self.permissions[channel][action_label]["deny"]).union(set(deny)));
    }

    can add_exception(action_label:str) {
        # adds an action to the exceptions list if it's not already present
        if action_label not in self.exceptions {
            self.exceptions.append(action_label);
        }
    }

    can in_session_group(session_id:str, group_names:list) {
        # checks if a session_id is in any of the session groups provided in the list
        for group_name in group_names {
            if(group_name in self.session_groups.keys()) {
                if(session_id in self.session_groups[group_name]) {
                    return True;
                }
            }
        }
        return False;
    }
    

    can has_action_access(session_id:str, action_label:str, channel:str="default") {
        # executes any attached and enabled whatsapp whitelist actions

        if(self.enabled) {
            # Check if channel exists in permissions
            if(channel in self.permissions.keys()) {
                 # First check specific action permission
                if(action_label in self.permissions[channel].keys()) {
                    # Deny rules are checked first for higher precedence
                    if("deny" in self.permissions[channel][action_label].keys()) {

                        if  "all" in self.permissions[channel][action_label]["deny"]
                            or session_id in self.permissions[channel][action_label]["deny"] 
                            or self.in_session_group(session_id, self.permissions[channel][action_label]["deny"]) {
                            return False;
                        }   
                    }

                    if("allow" in self.permissions[channel][action_label].keys()) {

                        if  "all" in self.permissions[channel][action_label]["allow"]
                            or session_id in self.permissions[channel][action_label]["allow"] 
                            or self.in_session_group(session_id, self.permissions[channel][action_label]["allow"]) {
                            return True;
                        }                      
                    }
 
                } elif("any" in self.permissions[channel].keys()) {
                    # Then check 'any' action permissions as a fallback

                    if("deny" in self.permissions[channel]['any'].keys()) {
                        
                        if  "all" in self.permissions[channel]['any']["deny"]
                            or session_id in self.permissions[channel]['any']["deny"] 
                            or self.in_session_group(session_id, self.permissions[channel]['any']["deny"]) {
                            return False;
                        }   

                    }

                    if("allow" in self.permissions[channel]['any'].keys()) {
                        
                        if  "all" in self.permissions[channel]['any']["allow"]
                            or session_id in self.permissions[channel]['any']["allow"] 
                            or self.in_session_group(session_id, self.permissions[channel]['any']["allow"]) {
                            return True;
                        }   

                    }
                    
                }
            }

            return False;
        } else {
            return True;
        }           
    }


    can healthcheck() -> bool {
        try {
            # Check if 'permissions' is a dict and has at least one key
            if (type(self.permissions) == dict && len(self.permissions.keys()) > 0) {
                # Define allowed and required keys
                allowed_channels = ["default", "whatsapp", "facebook"];
                required_channels = ["deny", "allow"];
                
                # Iterate over each channel in the 'permissions'
                for channel in self.permissions.keys() {
                    if (channel in allowed_channels) {
                        if ("any" in self.permissions[channel]) {
                            # Iterate over each access type in the channel permissions
                            for access in self.permissions[channel] {
                                # Get the resource value for this access
                                resource_value = self.permissions[channel][access];
                                
                                if (type(resource_value) == dict) {
                                    # Check each required access exists
                                    for required_channel in required_channels {
                                        if (required_channel not in resource_value) {
                                            return False;  # Missing required access
                                        }
                                    }
                                }
                                else {
                                    return False;  # Resource value is not a dict
                                }
                            }
                        }
                        else {
                            return False;  # 'any' key missing in channel
                        }
                    }
                    else {
                        return False;  # Channel not in allowed_channels
                    }
                }
                return True;  # All checks passed
            }
            return False;  # 'permissions' is not a dict or is empty
        } except Exception as e {
            self.logger.error(f"An exception occurred in {self.label}:\n{traceback.format_exc()}\n");
            return False;
        }
    }

}
