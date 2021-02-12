#!/usr/bin/env python3

from aws_cdk import core

from bb_fdns.bb_fdns_stack import BbFdnsStack


app = core.App()
BbFdnsStack(app, "bb-fdns")

app.synth()
