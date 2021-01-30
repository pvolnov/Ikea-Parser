from pathlib import Path
import json
from datetime import datetime, timedelta
from time import sleep
from app.logging_config import logger
from hashlib import sha1
import types


class Task:
    def __init__(self, name: str, func, args=None, kwargs=None, single=None,
                 interval: timedelta = None, start: datetime = None,
                 runs_count: int = None):
        if not func or (not single and not interval):
            raise ValueError('Unacceptable task settings. Specify interval or single arg')

        # Initial params
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.single = single
        self.interval = interval
        self.start = start
        self.runs_count = runs_count
        self.func = func

        # Current params
        self.last_exec_time: datetime = datetime.fromtimestamp(0)
        self.exec_count = 0

    def load_config(self, config: dict):
        if config:
            self.exec_count = config.get('exec_count', 0)
            self.last_exec_time = datetime.fromtimestamp(config.get('last_exec_time', datetime.now().timestamp()))

    def get_config(self):
        config = {
            'exec_count': self.exec_count,
            'last_exec_time': self.last_exec_time.timestamp()
        }
        return config

    def get_hash(self):
        return sha1(
            (self.name + str(self.single) + str(self.interval) + str(self.start)
             + str(self.runs_count) + str(self.kwargs) + str(self.args)
             ).encode()
        ).hexdigest()[:5]

    def is_finished(self):
        if self.single and self.exec_count:
            return True
        if self.runs_count and self.runs_count <= self.exec_count:
            return True
        return False

    def run(self):
        self.exec_count += 1
        logger.debug('Run task %s, exec_count: %s, args: %s, kwargs: %s', self.name, self.exec_count, self.args,
                     self.kwargs)
        self.last_exec_time = datetime.now()
        args = self.args or []
        kwargs = self.kwargs or {}
        result = self.func(*args, **kwargs)
        logger.debug('Duration: %s, result: %s', self.name, result)
        return result

    def iter_run(self):
        if self.is_finished():
            return
        if self.single or self.interval and datetime.now() - self.last_exec_time > self.interval:
            self.run()
            return True


class TaskManager:
    default_config_filename = 'tasks.json'

    def __init__(self, config_filename=None, update_interval: float = 1):
        if not config_filename:
            config_filename = self.default_config_filename

        self.config_filename = config_filename
        self.tasks = dict()
        self.config_dict = {
            'tasks': {}
        }
        self.load_config()
        self.sleep_sec = update_interval

    def load_config(self):
        if Path(self.config_filename).exists():
            with open(self.config_filename, 'r') as f:
                self.config_dict = json.load(f)

    def update_config_dict(self):
        self.config_dict['tasks'] = {
            task.get_hash(): task.get_config()
            for task in self.tasks.values()
        }

    def save_config(self):
        self.update_config_dict()

        with open(self.config_filename, 'w') as f:
            json.dump(self.config_dict, f, indent=4)

    def _insert_task(self, task: Task):
        task_config: dict = self.config_dict['tasks'].get(task.get_hash(), {})
        task.load_config(task_config)
        self.tasks[task.get_hash()] = task

    def add_task(self, task: Task):
        self._insert_task(task)

    def add_tasks(self, tasks):
        for task in tasks:
            self.add_task(task)

    def clear_tasks(self):
        for key in list(self.tasks.keys()):
            if self.tasks[key].is_finished():
                del self.tasks[key]

    def start(self):
        while True:
            for task in self.tasks.values():
                try:
                    is_launched = task.iter_run()
                    if is_launched:
                        self.save_config()
                except:
                    logger.exception('Fail task execution %s', task.name)
            self.save_config()
            self.clear_tasks()
            sleep(self.sleep_sec)

    def __del__(self):
        pass
