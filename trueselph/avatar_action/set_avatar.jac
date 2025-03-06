import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py base64;
import:jac from jivas.agent.core.agent { Agent }
import:jac from jivas.agent.action.action { Action }
import:jac from jivas.agent.action.actions { Actions }
import:jac from jivas.agent.action.interact_graph_walker { interact_graph_walker }


walker set_avatar :interact_graph_walker: {

    has files:list[dict] = [];
    has response:bool = False;

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled==True)(?label=='AvatarAction');
    }

    can on_action with Action entry {
        if self.files {

            for file in self.files {
                # Base64 encode the file content
                if( file_content_base64 := base64.b64encode(file['content']).decode('utf-8')) {
                    here.set_avatar_image(image_data = file_content_base64, mimetype = file['type']);
                    self.response = True;
                } 
            }
        }
    }

}