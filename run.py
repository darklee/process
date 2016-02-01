import io
import json
import logging
import os
import service

import psutil
from bottle import template, Bottle, response, JSONPlugin, request

logging.basicConfig(level=logging.INFO)

FILE_SERVICES = "services.json"
FILE_SETTINGS = "settings.json"

app = Bottle()
settings = json.load(io.open(FILE_SETTINGS, encoding="UTF-8"))


def before_request():
    response.set_header("Server", "Simple")


def after_request():
    if "charset=" not in response.content_type:
        response.content_type += ";charset=UTF-8"


@app.route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)


@app.route('/processes')
def processes():
    infos = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', "ppid"])
        except psutil.NoSuchProcess:
            pass
        else:
            infos.append(pinfo)
    if "map" in request.params:
        pmap = {}
        for info in infos:
            pid = info["pid"]
            pmap[pid] = info
        return {
            "data": pmap
        }
    else:
        return {
            "data": infos
        }


@app.get("/config")
def config():
    return settings


def do_auto_start_services():
    autostart = settings["services"].get("autostart", False)
    logging.info("Starting services, autostart=%s" % autostart)
    service_map = {}
    for conf in settings["services"]["list"]:
        srv = service.Service(conf)
        service_map[conf["id"]] = srv
    if autostart:
        for key in service_map:
            srv = service_map[key]
            srv.autostart()


class JsonPlugin(JSONPlugin):
    def __init__(self):
        def json_dumps(*args):
            return json.dumps(*args, ensure_ascii=False)

        self.json_dumps = json_dumps
        super(JsonPlugin, self).__init__()


do_auto_start_services()
app.config['autojson'] = False
app.add_hook("before_request", before_request)
app.add_hook("after_request", after_request)
app.install(JsonPlugin())
app.run(host='0.0.0.0', port=8080)
