
from dotenv import dotenv_values
from aws_cdk import (
    core, 
)
from collections import OrderedDict
from .common_resources import CommonResourceStack
from .stage_resources import StageResourceStack
from .app_pipeline import AppPipelineStack

class BackstageStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, props: dict, stages: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        crs = CommonResourceStack( self, "infra-common-resources", props)
        pipeline = AppPipelineStack(self, 'backstage-app-pipeline', props, crs)

        # we add deploy stages to the pipeline based on stages dict.
        for name,stage in stages.items():

            # dont pass these into the ECS container env.
            approval = stage.pop('STAGE_APPROVAL', False)
            emails = stage.pop('APPROVAL_EMAILS', None)
            # overload the shared env vars with those for the stage specifics if required. 
            props = {
                **props,
                **stage
            }
            srs = StageResourceStack(self, name, props, crs)

            # add a ECS deploy stage with the stage specific service, and an approval stage if requested.
            pipeline.add_deploy_stage(name, srs.ecs_stack.service, approval, emails)

        ### build a codepipeline for building new images and re-deploying to ecs
        ### this will use the backstage app repo as source to catch canges there
        ### execute a docker build and push image to ECR
        ### then execute ECS deployment
        ### once this pipeline is built we should only need to commit changes 
        ### to the backstage app repo to deploy and update

        # create the output artifact space for the pipeline
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # setup source to be the backstage app source
        source_action = actions.GitHubSourceAction(
            oauth_token=github_token_secret.secret_value_from_json("secret"),
            owner=github_org,
            repo=github_repo,
            branch='main',
            action_name="Github-Source",
            output=source_output
        )
        # make codebuild action to use buildspec.yml and feed in env vars from .env
        # this will build and push new image to ECR repo

        build_project = codebuild.PipelineProject(
            self, 
            "CodebuildProject", 
            build_spec=codebuild.BuildSpec.from_object(build_spec),
            #build_spec=codebuild.BuildSpec.from_source_filename('buildspec.yml'),
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_4_0, privileged=True),
        )
        policy =  iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
        build_project.role.add_managed_policy(policy)

        # code build action will use docker to build new image and push to ECR
        # the buildspec.yaml is in the backstage app repo
        repo_uri = docker_asset.repository.repository_uri

        build_action = actions.CodeBuildAction(
            action_name="Docker-Build",
            project=build_project,
            input=source_output,
            outputs=[build_output],
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(value=repo_uri),
                "AWS_REGION": codebuild.BuildEnvironmentVariable(value=props.get("AWS_REGION")),
                "CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value=props.get("CONTAINER_NAME"))
            },

        )
        # ECS deploy action will take file made in build stage and update the service with new image
        deploy_action = actions.EcsDeployAction(
            service=ecs_stack.service,
            action_name="ECS-Deploy",
            input=build_output,
        )

        pipeline = codepipeline.Pipeline(self, "fccbackstagepipeline", cross_account_keys=False)

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[deploy_action]
        )