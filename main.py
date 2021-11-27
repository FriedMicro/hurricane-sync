import psutil
import os
import math
import subprocess
import threading
import time
import pathlib

class GenericObj(object):
    pass

def generic_command(command):
    print("Running generic system call")

def rysnc_contents(source, config, mode):
    exclusions = config.short_exclusions
    destination = source.replace(config.source, config.destination)
    last_char_index = len(source) - 1
    if source[-2:] == "//":
        source = source[:-1]
    exclusion_string = ""
    if source == config.source:
        if len(exclusions) != 0:
            exclusion_string = " --delete-excluded "
        for exclusion in exclusions:
            exclusion_string += ("--exclude=" + exclusion + " ")
        print("Only excluding at root of: " + config.source)
    if mode == "net":
        rsync_command = "/usr/bin/sshpass -p 'password' /usr/bin/rsync --port=873 -avzz --delete " + exclusion_string + "'" + source + "/'" + " " + "'" + destination + "'"
    elif mode == "checksum":
        rsync_command = "/usr/bin/sshpass -p 'password' /usr/bin/rsync --port=873 -avzzc --delete " + exclusion_string + "'" + source + "/'" + " " + "'" + destination + "'"
    else:
        rsync_command = "/usr/bin/rsync -avW --no-recursive --dirs --inplace --delete " + exclusion_string + "'" + source + "/'" + " " + "'" + destination + "'"
    print(rsync_command)
    subprocess.run(rsync_command, shell=True)

def get_cpu_free():
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_usage_all = psutil.cpu_percent(interval=1, percpu=True)
    cpu_threads = os.cpu_count()
    percent_per_thread = 100 / cpu_threads
    cpu_reserve = 10
    threads_available = cpu_threads - math.ceil((cpu_usage + cpu_reserve) / percent_per_thread)
    return threads_available

def get_sync_directories():
    with open(script_path + "/" + "directories.txt") as file:
        lines = file.readlines()
        lines_data = []
        for line in lines:
            line_parts = line.rstrip().split(":::")
            if len(line_parts) > 1:
                source = line_parts[0]
                destination = line_parts[1]
                location = line_parts[2]

                config_data = GenericObj()
                config_data.source = source
                config_data.destination = destination
                config_data.location = location
                config_data.exclusions = []
                config_data.short_exclusions = []

                lines_data.append(config_data)
            else:
                index = len(lines_data) - 1
                exclusion = lines_data[index].source[:-1] + line.rstrip()
                lines_data[index].exclusions.append(exclusion)
                lines_data[index].short_exclusions.append(line.rstrip())
    for line in lines_data:
        print(line.exclusions)
    return lines_data

def get_top_level_directories(path):
    dirs_short = next(os.walk(path))[1]
    dirs_full = []
    for dir_short in dirs_short:
        if path[len(path) - 1] != "/":
            full_path = path + "/" + dir_short
        else:
            full_path = path + dir_short
        dirs_full.append(full_path)
    return dirs_full

def traverse_directories_top(config):
    source = config.source
    root_thread = dispatch_rsync(source, config)
    top_level_directories = get_top_level_directories(source)
    root_thread.join()
    if config.location != "net":
        for child in top_level_directories:
            if skip_exclusion(child, config) == False:
                print(child + " " + str(config.exclusions))
                x = threading.Thread(target=process_directory, args=(child, config,))
                x.start()

def process_directory(directory, config):
    root_thread = dispatch_rsync(directory, config)
    root_thread.join()
    children = get_top_level_directories(directory)
    for child in children:
        if skip_exclusion(child, config) == False:
            x = threading.Thread(target=process_directory, args=(child, config,))
            x.start()

available_threads = get_cpu_free()
active_threads = []
def dispatch_rsync(directory, config):
    while available_threads <= 0:
        for thread, index in enumerate(active_threads):
            if thread.is_alive() != True:
                active_threads.remove(index)
                ++available_threads
    x = threading.Thread(target=rysnc_contents, args=(directory, config, config.location,))
    x.start()
    --available_threads
    active_threads.append(x)
    return x

def skip_exclusion(child, config):
    exclusions = config.exclusions
    if child in exclusions:
        return True
    for exclusion in exclusions:
        if(child.startswith(exclusion)):
            return True
    return False

print("Available Threads: " + str(available_threads))
script_path = str(pathlib.Path(__file__).parent.resolve())
subprocess.run(["/usr/bin/bash", script_path + "/setup.sh"])
all_directories = get_sync_directories()
for directory in all_directories:
    x = threading.Thread(target=traverse_directories_top, args=(directory,))
    x.start()
subprocess.run(["/usr/bin/bash", script_path + "/teardown.sh"])