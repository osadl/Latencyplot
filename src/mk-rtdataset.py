#!/usr/bin/env python3

import os
import sys
import subprocess
import gzip
import json
from datetime import datetime, timezone

latencyfile = '/var/cache/latencyplot/histdata.txt'

def create(filename):
  rt = {}
  format = rt['format'] = {}
  format['name'] = 'RT Dataset'
  format['version'] = '1.0'

  timestamps = rt['timestamps'] = {}
  timestamps['origin'] = datetime.fromtimestamp(os.path.getctime(latencyfile)).astimezone().isoformat(timespec='seconds')
  timestamps['dataset'] = datetime.now().astimezone().isoformat(timespec='seconds')

  system = rt['system'] = {}
  p = subprocess.Popen('hostname', stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()
  p.wait()
  system['hostname'] = output.decode('utf-8').strip('\n')

  processor = rt['processor'] = {}
  f = open('/etc/qafarm/shortcpu', 'r')
  shortcpu = f.read().split(' ')
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

  kernel = rt['kernel'] = {}
  p = subprocess.Popen('uname -r', stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()
  p.wait()
  kernel['version'] = output.decode('utf-8').strip('\n')

  p = subprocess.Popen('/usr/local/bin/getpatches', stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()
  p.wait()
  patches = output.decode('utf-8').split('\n')
  kernel['patches'] = []
  for line in patches:
    line = line.strip('\n')
    if len(line) == 0:
      continue
    line = line.split('/')
    line = line[len(line) - 1]
    kernel['patches'].append(line)

  with gzip.open('/proc/config.gz', 'rb') as c:
    config = c.read().decode('utf-8').split('\n')
  kernel['config'] = []
  for line in config:
    line = line.strip('\n')
    if len(line) == 0 or line[0] == '#':
      continue
    kernel['config'].append(line)

  with open('/proc/cmdline', 'r') as c:
    kernel['cmdline'] = c.read().strip('\n')

  condition = rt['condition'] = {}
  condition['load'] = 'idle'
  condition['cycles'] = int(1E8)
  condition['interval'] = 200

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

  latency = rt['latency'] = {}
  latency['granularity'] = 'microseconds'
  cores = latency['cores'] = []

  h = open(latencyfile, 'r')
  lines = h.readlines()
  first = True
  for line in lines:
    line = line.strip('\n')
    if len(line) == 0 or line[0] == '#':
      continue
    values = line.split('\t')
    c = 0
    for value in values:
      if first:
        histogram = []
        cores.append(histogram)
      cores[c].append(int(value))
      c += 1
    first = False
  h.close()

  json_object = json.dumps(rt, indent=4)
  with open(filename, 'w') as outfile:
    outfile.write(json_object)

def main(argv):
  if len(argv) > 1:
    filename = argv[1]
  else:
    filename = 'rt.json'
  create(filename)

if __name__ == '__main__':
  main(sys.argv)
