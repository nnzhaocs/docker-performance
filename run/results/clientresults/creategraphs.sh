#!/bin/bash

python3 latencygraph.py -i dal_clientbmode0.json fra_clientbmode0.json lon_clientbmode0.json syd_clientbmode0.json -n "B mode 0";
python3 latencygraph.py -i dal_clientbmode3.json fra_clientbmode3.json syd_clientbmode3.json -n "B mode 3";
