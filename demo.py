# 这里需要引入三个模块
import os
import sched
import threading
import time

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间 
schedule = sched.scheduler(time.time, time.sleep)


def perform_command(cmd, inc):
    os.system(cmd)
    timming_exe("echo %time%", 2)


def timming_exe(cmd, inc=60):
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动 
    schedule.enter(inc, 0, perform_command, (cmd, inc))
    # 持续运行，直到计划时间队列变成空为止 
    schedule.run()


interval = 2
print("show time after %s seconds:" % interval)


def work():
    timming_exe("echo %time%", interval)


threading.Thread(target=work).start()
time.sleep(60)
quit()
