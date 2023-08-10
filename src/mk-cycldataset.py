#!/usr/bin/env python

# This software is licensed under GPL-3.0
# Copyright (c) 2023 Schneider Electric
# Authors Jean-françois Hugard <jean-francois.hugard@se.com>
#         Niels Jean-vincent <niels.jeanvincent@non.se.com>
# Based on mk-rtdataset.py from osadl/LatencyPlot repository
# Author Carsten Emde <C.Emde@osadl.org>

import os
import sys
import subprocess
import json
from datetime import datetime

latencyfile = '/var/cache/latencyplot/histdata.txt'
maximafile = '/var/cache/latencyplot/histmax.txt'
condition_load = 'idle'
cyclictest_command = ''

def create(filename):
    """Create JSON latency file "fileame" from data of the most recent cyclictest run."""
    global cyclictest_command, condition_load
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open(os.devnull, 'wb')

    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError

    rt = {}
    rtformat = rt['format-test'] = {}
    rtformat['name'] = 'RT Cyclictest'
    rtformat['version'] = '1.0'

    timestamps = rt['timestamps'] = {}
    p = subprocess.Popen('date -Iseconds', stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p.wait()
    tzoffset = '+' + output.decode('utf-8').split('+')[1].strip('\n')
    timestamps['origin'] = datetime.fromtimestamp(os.path.getctime(latencyfile)).isoformat().split('.')[0] + tzoffset
    now = datetime.now().isoformat()
    timestamps['dataset'] = now.split('.')[0] + tzoffset

    condition = rt['condition'] = {}
    condition['load'] = condition_load
    try:
        if (cyclictest_command == ''):
            f = open('/usr/local/bin/latencyplot', 'r')
            lines = f.readlines()
            for line in lines:
                if 'cycles=' in line:
                    cycles = line.split('=')[1].strip('\n')
                line = line.split('>')[0]
                if 'cyclictest' in line:
                    if '/bin/' in line:
                        line = line.split('/')
                        line = line[len(line)-1]
                    cyclictest_command = line.strip('\n').replace('$cycles', cycles).strip()
                    break
            f.close()
    except FileNotFoundError:
        print("/usr/local/bin/latencyplot not found !")
    finally:
        condition['cyclictest'] = cyclictest_command

    if 'cyclictest' in condition:
        loops = [s for s in condition['cyclictest'].split(' ') if s.startswith('-l')]
        interval = [s for s in condition['cyclictest'].split(' ') if s.startswith('-i')]
        if loops:
            condition['cycles'] = int(loops[0][2:])
        if interval:
            condition['interval'] = int(interval[0][2:])

    latency = rt['latency'] = {}
    latency['granularity'] = 'microseconds'
    cores = latency['cores'] = []
    maxima = latency['maxima'] = []
    loops = []
    h = open(latencyfile, 'r')
    lines = h.readlines()
    first = True
    for line in lines:
        line = line.strip('\n')
        if len(line) == 0:
            continue
        if line.startswith('# Max Latencies:'):
            maxline = line.split(':')[1].strip()
            for maxvalues in maxline.split(' '):
                maxima.append(int(maxvalues))
        if line.startswith('# Total:'):
            cycles = line.split(':')[1].strip()
            for cycle in cycles.split(' '):
                loops.append(int(cycle))  
        
        if line[0] == '#':
            continue
        values = line.replace(' ', '\t').split('\t')
        c = 0
        for value in values:
            if first:
                histogram = []
                cores.append(histogram)
            cores[c].append(int(value))
            c += 1
        first = False
    h.close()

    # If not, get cycles from the latency file
    if 'cycles' not in condition:
        condition['cycles'] = max(loops)

    try:
        m = open(maximafile, 'r')
        for maximum in m.read().strip('\n').split('\n'):
            maxima.append(int(maximum))
        m.close()
    except FileNotFoundError:
        print(maximafile, " file not found!")

    try:
        json_object = json.dumps(rt, indent=4)
    except:
        json_object = json.write(rt)
    outfile = open(filename, 'w')
    outfile.write(json_object)
    outfile.close()

def main(argv):
    global cyclictest_command, condition_load
    if len(argv) > 1:
        filename = argv[1]
        if len(argv) > 2:
            condition_load = argv[2]
            if (len(argv) > 3):
                cyclictest_command = argv[3]
    else:
        filename = 'rt.json'
    create(filename)

if __name__ == '__main__':
    main(sys.argv)
