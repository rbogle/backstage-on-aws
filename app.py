#!/usr/bin/env python3

from aws_cdk import core
import yaml
from infra.backstage import BackstageStack
from infra.infra_pipeline import InfraPipelineStack

# load yaml file and get key=value for env vars
with open("./configs/env-config.yaml") as conf_file:
    config = yaml.full_load(conf_file)

# we want to fail here if these keys are not there
props = config['common']
stages = config['stages']

# start the naming circus
stack_name = props.get('TAG_STACK_NAME', 'backstage')

stacks = [
    f"{stack_name}-pipeline",
    stack_name
]

# Using a hosted dns zone requires specifying account and region, 
# you will need active credentials for this account to synth/deploy
env =core.Environment(account=props.get('AWS_ACCOUNT'), region=props.get('AWS_REGION', 'us-east-1'))

app = core.App()
infra_pipeline = InfraPipelineStack(app, stacks[0] , stacks=stacks ,props=props, env=env)
backstage_infra = BackstageStack(app, stacks[1], props=props, stages=stages, env=env)

# be nice and tag all these resources so their are attributable
core.Tags.of(app).add("Name",stack_name)
core.Tags.of(app).add("Product",props.get('TAG_STACK_PRODUCT', 'dev-portal'))


app.synth()
