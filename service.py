import os
import logging
import psutil
import io


class Service:
    def __init__(self, conf):
        self.conf = conf
        self.pid_file = "services/{0}.pid".format(conf["id"])
        self.process_list = []
        if os.path.exists(self.pid_file):
            root_pid = int(io.open(self.pid_file).read())
            pass

    def autostart(self):
        if self.conf.get("autostart", True):
            logging.info("Autostart: %s, cmd=%s" % (self.conf["id"], self.conf["cmd"]))
            psutil.Popen(self.conf["cmd"])
        else:
            logging.info("Autostart disabled: %s" % self.conf["id"])
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def restart(self):
        pass
