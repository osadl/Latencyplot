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
import gzip
import json


def create(filename):
    """Create JSON information file "filename" about system environment."""

    msgNotAvailable = "Not available, to be manually set"
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open(os.devnull, 'wb')

    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError

    rt = {}
    
    rtformat = rt['format-conf'] = {}
    rtformat['name'] = 'RT Configuration'
    rtformat['version'] = '1.0'

    system = rt['system'] = {}
    p = subprocess.Popen('hostname', stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p.wait()
    system['hostname'] = output.decode('utf-8').strip('\n')


    processor = rt['processor'] = {}

    processor['clock'] = msgNotAvailable 
    processor['family'] = msgNotAvailable 
    processor['vendor'] = msgNotAvailable 
    processor['type'] = msgNotAvailable 

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
    kernel['version'] = msgNotAvailable
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
    config = ''
    try:
        c = gzip.open('/proc/config.gz', 'rb')
        config = c.read().decode('utf-8').split('\n')
        c.close()
    except FileNotFoundError:
        try:
            c = open('/boot/config-' + kernel['version'], 'r')
            config = c.read().split('\n')
            c.close()
        except FileNotFoundError:
            pass
    if config != '':
        for line in config:
            line = line.strip('\n')
            if len(line) == 0 or line[0] == '#':
                continue
            kernel['config'].append(line)

    c = open('/proc/cmdline', 'r')
    kernel['cmdline'] = c.read().strip('\n')
    c.close()

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
