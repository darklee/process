import io
import json
import logging

import psutil
from bottle import template, Bottle, response, JSONPlugin, request

app = Bottle()
settings = json.load(io.open("settings.json", encoding="UTF-8"))


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
    if "tree" in request.params or "map" in request.params:
        pmap = {}
        for info in infos:
            pid = info["pid"]
            ppid = info["ppid"]
            pp = pmap.get(ppid, {
                "subprocesses": []
            })
            p = pmap.get(pid, {
                "subprocesses": []
            })
            pmap[ppid] = pp
            pmap[pid] = p
            p.update(info)
            if ppid == pid:
                del p["ppid"]
            subprocesses = pp["subprocesses"]
            subprocesses.append(pid)
        if "map" in request.params:
            return {
                "data": pmap
            }
        else:
            roots = []

            def process_sub(p):
                subs = p["subprocesses"]
                for x in range(0, len(subs)):
                    sub = pmap[subs[x]]
                    subs[x] = pmap[subs[x]]
                    process_sub(sub)

            for k in pmap:
                p = pmap[k]
                if "ppid" not in p:
                    roots.append(p)
                process_sub(p)
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


logging.basicConfig(level=logging.INFO)


def do_auto_start():
    logging.info("Autostarting")
    for pdef in settings["process"]["list"]:
        autostart = pdef.get("autostart", settings["process"].get("autostart", False))
        if autostart:
            logging.info("Autostart: id=%s, cmd=%s" % (pdef["id"], pdef["cmd"]))
            psutil.Popen(pdef["cmd"])


class JsonPlugin(JSONPlugin):
    def __init__(self):
        def json_dumps(*args):
            return json.dumps(*args, ensure_ascii=False)

        self.json_dumps = json_dumps


do_auto_start()
app.config['autojson'] = False
app.add_hook("before_request", before_request)
app.add_hook("after_request", after_request)
app.install(JsonPlugin())
app.run(host='0.0.0.0', port=8080)
