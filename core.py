import io
import json
import logging
import os
import sched
import threading
import time

import psutil


class Service:
    logger = logging.getLogger("service")

    def __init__(self, options):
        self.options = options
        self.id = options["id"]
        self.logger = Service.logger.getChild(str(self.id))
        os.makedirs("runtime", exist_ok=True)
        self.pid_file = "runtime/{0}.pid".format(options["id"])
        self.process_list = []
        self.running = False
        if os.path.exists(self.pid_file):
            pid_list = list(json.load(io.open(self.pid_file, encoding="UTF-8")))
            self.logger.info("Loading pid: %s", pid_list)
            for pid in pid_list:
                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    if proc.cmdline() == self.options["cmd"]:
                        self.logger.info("Found running process: %s", pid)
                        self.process_list.append(proc)
                        self.running = True
                if not self.running:
                    self.logger.info("Process is not running: %s", pid)

    def autostart(self):
        if self.options.get("autostart", True):
            self.start()
        else:
            self.logger.info("Autostart disabled")

    def start(self):
        if not self.running:
            self.logger.info("Starting: %s" % self.options["cmd"])
            self.process_list.append(psutil.Popen(self.options["cmd"]))
            for proc in self.process_list:
                self.logger.info("Started: %s" % proc.pid)
            self.running = True
            json.dump(list(map(lambda x: x.pid, self.process_list)), io.open(self.pid_file, mode="w", encoding="UTF-8"))

    def stop(self):
        process_list = self.process_list.copy()
        self.process_list.clear()
        for proc in process_list:
            if proc.is_running():
                proc.terminate()
        remaining_time = 30
        start_time = time.time()
        for proc in process_list:
            remaining_time = remaining_time - (time.time() - start_time)
            proc.wait(remaining_time)
        for proc in process_list:
            if proc.is_running():
                proc.kill()
        self.running = False

    def restart(self):
        self.stop()
        self.start()


class Console:
    logger = logging.getLogger("console")

    def __init__(self, options):
        self.logger = Console.logger
        self._services = {}
        self._options = options
        self._scheduler = sched.scheduler(time.time, time.sleep)
        threading.Thread(target=self._monitor, daemon=True).start()

    def start(self):
        service_conf_list = self._options["services"]["list"]
        self.logger.info(
            "Loaded %s services %s" % (len(service_conf_list), list(map(lambda x: x["id"], service_conf_list))))
        self.logger.info("Starting services")
        for conf in service_conf_list:
            srv = Service(conf)
            self._services[conf["id"]] = srv
        for key in self._services:
            srv = self._services[key]
            srv.autostart()

    def get_service(self, service_id):
        return self._services.get(service_id)

    def get_services(self):
        return self._services

    def _monitor(self):
        self.logger.debug("Check running services")
        try:
            for k in self._services:
                srv = self._services[k]
                for proc in srv.process_list:
                    if not proc.is_running():
                        self.logger.info("Process stopped, try restarting %s" % srv.id)
                        srv.restart()
        finally:
            self._scheduler.enter(5, 1, self._monitor)
            self._scheduler.run()
