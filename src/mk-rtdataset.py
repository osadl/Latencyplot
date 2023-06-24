#!/usr/bin/env python

# This software is licensed under GPL-3.0
# Copyright (c) 2023 Open Source Automation Development Lab (OSADL) eG <info@osadl.org>
# Author Carsten Emde <C.Emde@osadl.org>

# Maintain Python 2.x compatibility
# pylint: disable=consider-using-with,unspecified-encoding

import os
import sys
import subprocess
import gzip
import json
from datetime import datetime

latencyfile = '/var/cache/latencyplot/histdata.txt'
maximafile = '/var/cache/latencyplot/histmax.txt'

def create(filename):
    """Create JSON latency file "fileame" from data of the most recent cyclictest run."""
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open(os.devnull, 'wb')

    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError

    rt = {}
    rtformat = rt['format'] = {}
    rtformat['name'] = 'RT Dataset'
    rtformat['version'] = '1.0'

    timestamps = rt['timestamps'] = {}
    p = subprocess.Popen('date -Iseconds', stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p.wait()
    tzoffset = '+' + output.decode('utf-8').split('+')[1].strip('\n')
    timestamps['origin'] = datetime.fromtimestamp(os.path.getctime(latencyfile)).isoformat().split('.')[0] + tzoffset
    now = datetime.now().isoformat()
    timestamps['dataset'] = now.split('.')[0] + tzoffset

    system = rt['system'] = {}
    p = subprocess.Popen('hostname', stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p.wait()
    system['hostname'] = output.decode('utf-8').strip('\n')

    processor = rt['processor'] = {}
    try:
        f = open('/etc/qafarm/shortcpu', 'r')
        shortcpu = f.read()
        processor['clock'] = shortcpu.split('@')[1].split(' ')[0]
        shortcpu = shortcpu.split(' ')
        processor['family'] = shortcpu[0]
        processor['vendor'] = shortcpu[1]
        n = 2
        processor['type'] = ''
        while shortcpu[n][0] != '@':
            if n > 2:
                processor['type'] = processor['type'] + ' '
            processor['type'] = processor['type'] + shortcpu[n]
            n = n + 1
        f.close()
    except FileNotFoundError:
        p = subprocess.Popen('uname -m', stdout=subprocess.PIPE, stderr=DEVNULL, shell=True)
        (output, err) = p.communicate()
        p.wait()
        processor['family'] = output.decode('utf-8').strip('\n')
        p = subprocess.Popen('cat /proc/cpuinfo', stdout=subprocess.PIPE, stderr=DEVNULL, shell=True)
        (output, err) = p.communicate()
        p.wait()
        cpuinfo = output.decode('utf-8').split('\n')
        for c in cpuinfo:
            if c.startswith('Hardware'):
                hw = c.split(':')[1].strip().split(' ')
                processor['vendor'] = hw[0]
                processor['type'] = hw[1]
                break
        if 'vendor' not in processor.keys():
            for c in cpuinfo:
                if c.startswith('model name'):
                    model = c.split(':')[1].strip().split(' ')
                    processor['vendor'] = model[0].split('(')[0]
                    processor['type'] = model[2]
                    clock = model[model.index('@') + 1]
                    if clock.endswith('GHz'):
                        clock = str(int(float(clock[:-3]) * 1000))
                    processor['clock'] = clock
                    break

    kernel = rt['kernel'] = {}
    p = subprocess.Popen('uname -r', stdout=subprocess.PIPE, stderr=DEVNULL, shell=True)
    (output, err) = p.communicate()
    p.wait()
    kernel['version'] = output.decode('utf-8').strip('\n')

    p = subprocess.Popen('/usr/local/bin/getpatches', stdout=subprocess.PIPE, stderr=DEVNULL, shell=True)
    (output, err) = p.communicate()
    p.wait()
    patches = output.decode('utf-8').split('\n')
    if patches[0]:
        kernel['patches'] = []
        for line in patches:
            line = line.strip('\n')
            if len(line) == 0:
                continue
            line = line.split('/')
            line = line[len(line) - 1]
            kernel['patches'].append(line)

    kernel['config'] = []
    try:
        c = gzip.open('/proc/config.gz', 'rb')
        config = c.read().decode('utf-8').split('\n')
        c.close()
    except FileNotFoundError:
        try:
            c = open('/boot/config-' + kernel['version'], 'r')
            config = c.read().decode('utf-8').split('\n')
            c.close()
        except FileNotFoundError:
            pass
    if config:
        for line in config:
            line = line.strip('\n')
            if len(line) == 0 or line[0] == '#':
                continue
            kernel['config'].append(line)

    c = open('/proc/cmdline', 'r')
    kernel['cmdline'] = c.read().strip('\n')
    c.close()

    condition = rt['condition'] = {}
    condition['load'] = 'idle'

    f = open('/usr/local/bin/latencyplot', 'r')
    lines = f.readlines()
    for line in lines:
        if 'cycles=' in line:
            cycles = line.split('=')[1].strip('\n')
        if 'cyclictest' in line:
            if '/bin/' in line:
                line = line.split('/')
                line = line[len(line)-1]
            condition['cyclictest'] = line.strip('\n').replace('$cycles', cycles).split('>')[0].strip()
            break
    f.close()
    if 'cyclictest' in condition:
        loops = [s for s in condition['cyclictest'].split(' ') if s.startswith('-l')]
        interval = [s for s in condition['cyclictest'].split(' ') if s.startswith('-i')]
        if loops:
            condition['cycles'] = int(loops[0][2:])
        if interval:
            condition['interval'] = int(interval[0][2:])
    if not 'cycles' in condition:
        condition['cycles'] = int(1E8)
    if not 'interval' in condition:
        condition['interval'] = 200

    latency = rt['latency'] = {}
    latency['granularity'] = 'microseconds'
    cores = latency['cores'] = []
    maxima = latency['maxima'] = []
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
    if len(maxima) == 0:
        m = open(maximafile, 'r')
        for maximum in m.read().strip('\n').split('\n'):
            maxima.append(int(maximum))
        m.close()

    try:
        json_object = json.dumps(rt, indent=4)
    except:
        json_object = json.write(rt)
    outfile = open(filename, 'w')
    outfile.write(json_object)
    outfile.close()

def main(argv):
    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = 'rt.json'
    create(filename)

if __name__ == '__main__':
    main(sys.argv)
