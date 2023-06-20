#!/usr/bin/env python3

# This software is licensed under GPL-3.0
# Copyright (c) 2023 Open Source Automation Development Lab (OSADL) eG <info@osadl.org>
# Author Carsten Emde <C.Emde@osadl.org>

import sys
import json
import matplotlib.pyplot as plt
import matplotlib.ticker
import xml.etree.ElementTree as ET
from io import BytesIO

ET.register_namespace("", "http://www.w3.org/2000/svg")

def maxlat(x, y):
    maximum = 0
    for lat in x:
        if lat == max(x):
            break
        if y[lat] > 0:
            maximum = lat
    return maximum

def plot(infilename, outfilename):
    """Read JSON data from "infilename" and create latency histogram "outfilename" with format derived from file name suffix."""
    with open(infilename, 'r', encoding='utf-8') as f:
        rt = json.load(f)
    cores = rt['latency']['cores']
    cores[0].append(max(cores[0]) + 1)

    fig, ax = plt.subplots()
    fig.set_figwidth(16)
    fig.set_figheight(9)

    try:
        rt['kernel']['patches']
        patched = 'patched '
    except:
        patched = ''
    plt.title('Latency histogram of ' + rt['system']['hostname'].split('.')[0] + ' with ' + rt['processor']['vendor'] +
     ' ' + rt['processor']['type'] + ' (' + rt['processor']['family'] + '), ' + patched + 'kernel ' + rt['kernel']['version'], fontsize=14)
    plt.yscale('log')
    plt.ylim(0.8E0, rt['condition']['cycles'])
    plt.ylabel('Number of samples per latency class')
    maxofmax = 0
    containers = []
    for i in range(1, len(cores)):
        if len(rt['latency']['maxima']) == 0:
            maxofcore = maxlat(cores[0], cores[i])
        else:
            maxofcore = rt['latency']['maxima'][i-1]
        if maxofcore > maxofmax:
            maxofmax = maxofcore
            coreofmax = i
        if i <= 10:
            space = '  '
        else:
            space = ''
        container = ax.stairs(cores[i], cores[0], label='Core ■' + str(i-1) + ': ' + space + str(maxofcore) + ' µs')
        containers.append(container)
    plt.xlabel('Maximum latency: ' + str(maxofmax) + ' µs, with "' + rt['condition']['cyclictest'] + '" on ' + rt['timestamps']['origin'].split('T')[0])
    plt.margins(0, 0)
    plt.locator_params(axis = 'x', nbins = 8)
    ax.yaxis.set_minor_locator(matplotlib.ticker.LogLocator(base=10.0, subs=(0.2,0.4,0.6,0.8), numticks=12))
    ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10.0, numticks=10))
    leg = plt.legend(ncol=6)
    plt.legend(ncol=6).get_texts()[coreofmax - 1].set_fontweight('bold')

    if outfilename != '':
        suffix = outfilename.split('.')
        suffix = suffix[len(suffix) - 1]
    else:
        suffix = ''

    if suffix == 'svg':

        for i in range(0, len(containers)):
            containers[i].set_gid(f'stairs_{i}')

        f = BytesIO()
        plt.savefig(f, format="svg")

        tree, xmlid = ET.XMLID(f.getvalue())

        legend1 = xmlid['legend_1']
        text1 = 0
        line1 = 0
        for child in legend1:
            id = child.attrib['id']
            if text1 == 0 and id.startswith('text_'):
                 text1 = int(id.split('_')[1])
            if line1 == 0 and id.startswith('line2d_'):
                 line1 = int(id.split('_')[1])
            if text1 != 0 and line1 != 0:
                break;

        offsets = []
        offsets.append(text1)
        offsets.append(line1)

        texts = leg.get_texts()
        for i in range(0, len(texts)):
            el = xmlid[f'text_{i+text1}']
            el.set('cursor', 'pointer')
            el.set('onclick', "toggle_stairsfromtext(this)")
            el.set('style', 'opacity: 1;')
            el = xmlid[f'line2d_{i+line1}']
            el.set('cursor', 'pointer')
            el.set('onclick', "toggle_stairsfromline(this)")
            el.set('style', 'opacity: 1;')

        script = """
<script type="text/javascript">
<![CDATA[
var offsets = %s;
function toggle(oid, attribute, values) {
    var obj = document.getElementById(oid);
    var a = obj.style[attribute];

    a = (a == values[0] || a == "") ? values[1] : values[0];
    obj.style[attribute] = a;
}

function toggle_stairsfromtext(obj) {
    var num = obj.id.split('_')[1];

    toggle('text_' + num, 'opacity', [1, 0.5]);
    toggle('stairs_' + (parseInt(num) - offsets[0]), 'opacity', [1, 0]);
}

function toggle_stairsfromline(obj) {
    var num = obj.id.split('_')[1];

    toggle('line2d_' + num, 'opacity', [1, 0.5]);
    toggle('stairs_' + (parseInt(num) - offsets[1]), 'opacity', [1, 0]);
}
]]>
</script>
""" % json.dumps(offsets)

        css = tree.find('.//{http://www.w3.org/2000/svg}style')
        css.text = css.text + "g {-webkit-transition:opacity 0.4s ease-out;" + \
            "-moz-transition:opacity 0.4s ease-out;}"

        tree.insert(0, ET.XML(script))

        ET.ElementTree(tree).write(outfilename)

    else:
        if len(outfilename) == 0:
            plt.show()
        else:
            plt.savefig(outfilename)

def main(argv):
    if len(argv) > 1:
        infilename = argv[1]
    else:
        infilename = 'rt.json'
    if len(argv) > 2:
        outfilename = argv[2]
    else:
        outfilename = ''
    plot(infilename, outfilename)

if __name__ == '__main__':
    main(sys.argv)
