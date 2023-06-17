# Latencyplot
Define a JSON file format for data exchange and provide example scripts how to create such files and generate a graph from them.

* [Purpose](#purpose)
* [Data format](#data-format)

## Purpose
Create a basis for sharing data of Linux PREEMPT_RT real-time systems

## Data format
```json
{
    "format": {
        "name": "RT Dataset",
        "version": "1.0"
    },
    "timestamps": {
        "origin": <ISO creation date of data>,
        "dataset": <ISO creation date of this file>
    },
    "system": {
        "hostname": <Name of the host undergoing the latency test>
    },
    "processor": {
        "family": <Processor family>,
        "vendor": <Processor vendor>,
        "type": <Processor type>
    },
    "kernel": {
        "version": <Kernel version>,
        "config": [
            <Array of subsequent non-emtpy non-comment lines of the the kernel configuration>
        ],
        "cmdline": <Kernel command line>
    },
    "condition": {
        "load": <System load conditions: "idle", "moderate", "heaavy" or "brute-force">
        "cycles": <Total number of cyclictest cycles>,
        "interval": <Cyclictest interval in µs>,
        "cyclictest": <Cyclictest command line>
    },
    "latency": {
        "granularity": <Width of class of latency data>
        "cores": [
            [
                <Two dimensional array of number of samples per latency class and per core>  
            ]
        ]
    }
}
```
