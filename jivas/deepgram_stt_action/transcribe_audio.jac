import:jac from agent.core.agent { Agent }
import:jac from agent.action.action { Action }
import:jac from agent.action.actions { Actions }
import:jac from agent.action.interact_graph_walker { interact_graph_walker }
import:py os;
import:py uuid;
import:py base64;

walker transcribe_audio :interact_graph_walker: {
    has files: list[dict] = [];

    can on_agent with Agent entry {
        visit [-->](`?Actions);
    }

    can on_actions with Actions entry {
        visit [-->](`?Action)(?enabled == True)(?label == 'DeepgramSTTAction');
    }

    can on_action with Action entry {
        if not self.files {
            self.response = {"success": False, "message": "No audio file provided"};
        } else {
            file = self.files[0];

            if ('audio' in file['type']
                or file['type'] == "application/octet-stream") {
                result = here.invoke_file(
                    audio_content=file['content'],
                    audio_type=file['type']
                );
                self.response = {
                    "success": True,
                    "duration": result["duration"],
                    "transcript": result["transcript"]
                };
            } else {
                self.response = {
                    "success": False,
                    "message": "Invalid file type, must be audio"
                };
            }
        }

    }
}
