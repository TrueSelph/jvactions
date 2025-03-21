import:py schedule;
import:py logging;
import:py traceback;
import:py from logging { Logger }
import:py from jvserve.lib.agent_interface { AgentInterface }
import:py from jvserve.lib.agent_pulse { AgentPulse }
import:jac from agent.action.action { Action }

node PulseAction :Action: {
    # Registers a cron-like job to trigger agent actions on an interval.

    # set up logger
    static has logger:Logger = logging.getLogger(__name__);

    has enabled:bool = False;
    # schedule of cron jobs by action
    has config:dict = {
        # accepts key:value mappings as expressed below
        # (see https://schedule.readthedocs.io/en/stable/examples.html)

        # 'PulseAction' : 'every(5).seconds',
        # 'XYZAction': 'every(1).hour.until("2030-01-01 18:00")'
    };

    can on_register() {

        # need to make ctx transient since it messes with YAML export
        self.transient_attrs += ['ctx'];
        # set up the schedule based on the config
        self.init_schedule();
    }

    can on_deregister() {
        # cancel all jobs tagged by 'action'
        schedule.clear('pulse-actions');
        # stop the pulse
        AgentPulse.stop();
    }

    can on_disable() {
        AgentPulse.stop();
    }

    can on_enable() {
        AgentPulse.start();
    }

    can postupdate() {
        # stop the pulse
        AgentPulse.stop();
        # clear all scheduled items
        schedule.clear('pulse-actions');
        # re-init the schedule
        self.init_schedule();
    }

    can pulse() {
        self.logger.info('pulsing..');
    }

    can init_schedule() {
        # sets up all scheduled jobs based on schedule config

        for action_label in self.config.keys() {
            self.queue_action_pulse(action_label=action_label, interval=self.config[action_label]);
        }

        # if we have jobs, start the thread
        jobs = schedule.get_jobs('pulse-actions');

        if(len(jobs) > 0 and self.enabled) {
            # has safety checks to prevent spamming
            AgentPulse.start();
        }
    }

    can queue_action_pulse(action_label:str, interval:str) {
        # accepts the action and time interval spec (see https://schedule.readthedocs.io/en/stable/examples.html)
        # then prepares the queued job
        try {
            # we'll need the agent_id of this action
            agent_id = self.get_agent().id;
            # we're using exec so it may get wild...
            # let's ensure we clear any preexisting jobs under the tag 'action_label'
            schedule.clear(action_label);
            # now, prepare the schedule statement
            exec_str = f'schedule.{interval}.do(AgentInterface.api_pulse, "action_label={action_label}", "agent_id={agent_id}").tag("pulse-actions", "{action_label}")';
            # let errr rip..
            return exec(exec_str);
        } except Exception as e {
            self.logger.error(f"an exception occurred, {traceback.format_exc()}");
        }
    }

}