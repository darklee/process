import io
import json
import logging

import psutil
from bottle import template, Bottle, response, JSONPlugin, request

import core

logging.basicConfig(level=logging.INFO)

FILE_SETTINGS = "settings.json"

settings = json.load(io.open(FILE_SETTINGS, encoding="UTF-8"))
console = core.Console(settings)
app = Bottle()


def before_request():
    response.set_header("Server", "Simple")


def after_request():
    if "charset=" not in response.content_type:
        response.content_type += ";charset=UTF-8"


@app.route('/hello/<name>')
def get_index(name):
    return template('<b>Hello {{name}}</b>!', name=name)


@app.route('/services')
def get_services():
    data = []
    services = console.get_services()
    for k in services:
        data.append(get_service_by_id(services[k].id)["data"])
    return {
        "data": data
    }


@app.route('/services/<service_id>')
def get_service_by_id(service_id):
    svr = console.get_service(service_id)
    if svr:
        data = {}
        data.update(svr.options)
        data["running"] = svr.running
        process_list = data["processes"] = []
        for proc in svr.process_list:
            process_list.append({
                "pid": proc.pid
            })
        return {
            "data": data
        }
    else:
        return None


@app.route('/action/service/<name>')
def do_service_action(name):
    service_id = request.params.get("id")
    svr = console.get_service(service_id)
    if svr:
        method = getattr(svr, name)
        if method:
            method()


@app.route('/processes')
def get_processes():
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
def get_config():
    return settings


def do_auto_start_services():
    autostart = settings["services"].get("autostart", False)
    logging.info("Autostart=%s" % autostart)
    if autostart:
        console.start()


class JsonPlugin(JSONPlugin):
    def __init__(self):
        def json_dumps(*args):
            return json.dumps(*args, ensure_ascii=False)

        self.json_dumps = json_dumps
        super(JsonPlugin, self).__init__()


if __name__ == "__main__":
    do_auto_start_services()
    app.config['autojson'] = False
    app.add_hook("before_request", before_request)
    app.add_hook("after_request", after_request)
    app.install(JsonPlugin())
    app.run(host='0.0.0.0', port=8080)
