#!/usr/bin/env python3

from aws_cdk import core
from dotenv import dotenv_values
from infra.backstage import BackstageStack

props = dotenv_values()
stack_name = props.get('TAG_STACK_NAME', 'backstage')

# Using a hosted dns zone requires specifying account and region 
env =core.Environment(account=props.get('AWS_ACCOUNT'), region=props.get('AWS_REGION', 'us-east-1'))

app = core.App()
backstage = BackstageStack(app, stack_name, props, env=env)

# be nice and tag all these resources so their are attributable
core.Tags.of(backstage).add("Stack:Name",stack_name)
core.Tags.of(backstage).add("Stack:Author",props.get('TAG_STACK_AUTHOR', 'foo.bar@example.com'))

app.synth()
