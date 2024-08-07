import datetime
import logging
import multiprocessing

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from .alert_manager import AlertManager
from .config import SchedulerConfig

class Scheduler():

    def __init__(self, scheduler_config: SchedulerConfig, queue: multiprocessing.Queue, alert_manager: AlertManager):
        self.scheduler = BackgroundScheduler()
        jobstores = {
            'default': SQLAlchemyJobStore(url=scheduler_config.conn_str)
        }
        # TODO: make executors configurable
        executors = {
            'default': {'type': 'threadpool', 'max_workers': 1},
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        self.scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
        self.queue = queue
        self.logger = logging.getLogger("scheduler")
        self.alert_manager = alert_manager

    def add_job(self, id, msg, time):
        now = datetime.datetime.now()
        # if max time already exist, delay messaging as there might be message unprocessed (i.e. using historic data)
        delay = datetime.timedelta(seconds=10)
        if time < now:
            time = now + delay
        self.scheduler.add_job(self.alert_manager.alert, 'date', args=[msg], next_run_time=time, id=id, replace_existing=True)

    def remove_job(self, id):
        try:
            self.scheduler.remove_job(id)
        except:
            self.logger.debug(f"removing id {id} not found")

    def scheduler_process(self):
        self.scheduler.start()
        while True:
            # TODO: write serializer class for scheduler command
            (command, *args) = self.queue.get()
            match command:
                case "add":
                    (id, time, msg) = args
                    self.add_job(id, msg, time)
                case "remove":
                    id = args
                    self.remove_job(id)
