#!/bin/bash

ryu-manager controllerz1.py --observe-links --ofp-tcp-listen-port 6633 &
ryu-manager controllerz1.py --observe-links --ofp-tcp-listen-port 6634 &
ryu-manager controllerz1.py --observe-links --ofp-tcp-listen-port 6635  &
