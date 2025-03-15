import:py schedule;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:jac from jivas.agent.action.action { Action }

node AvatarAction :Action: {
    # Registers a cron-like job to trigger agent actions on an interval.

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has image_data:str = "";
    has mimetype:str = "";

    can set_avatar_image(image_data:str, mimetype:str) {
        self.image_data = image_data;
        self.mimetype = mimetype;
    }

    can get_avatar_image() {
        if self.image_data {
            return (self.image_data, self.mimetype);
        } else {
            return None;
        }
    }

}