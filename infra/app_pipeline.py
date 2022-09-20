import yaml
from aws_cdk import (
    core, 
    aws_ecs as ecs,
    aws_iam as iam,
    aws_secretsmanager as secrets,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
    aws_chatbot as chatbot
)
from .common_resources import CommonResourceStack


class AppPipelineStack(core.Construct):

    def __init__(self, scope: core.Construct, id: str, props: dict, crs: CommonResourceStack) -> None:
        super().__init__(scope, id)
        # github info for codepipeline
        github_repo = props.get("GITHUB_APP_REPO")
        github_org = props.get("GITHUB_ORG")
        github_branch = props.get("GITHUB_APP_BRANCH", "main")
        codestar_connection_arn = props.get("CODESTAR_CONN_ARN")
        github_app_arn = props.get("GITHUB_APP_ARN")
        codestar_notify_arn = props.get("CODESTAR_NOTIFY_ARN")
        ### build a codepipeline for building new images and re-deploying to ecs
        ### this will use the backstage app repo as source to catch canges there
        ### execute a docker build and push image to ECR
        ### then execute ECS deployment
        ### once this pipeline is built we should only need to commit changes 
        ### to the backstage app repo to deploy and update

        # because this pipeline uses a different repo as source
        # we need to statically allocate the buildscript from an object 
        # rather than just pass the file from source.  
        with open(r'./app-buildspec.yml') as file:
            build_spec = yaml.full_load(file)

        # create the output artifact space for the pipeline
        self.source_output = codepipeline.Artifact()
        self.build_output = codepipeline.Artifact()

        # setup source to be the backstage app source
        source_action = actions.CodeStarConnectionsSourceAction(
            action_name="Github-Source",
            connection_arn=codestar_connection_arn,
            repo=github_repo,
            owner=github_org,
            branch=github_branch,
            output=self.source_output
        )

        # make codebuild action to use buildspec.yml and feed in env vars from .env
        # this will build and push new image to ECR repo

        build_project = codebuild.PipelineProject(
            self, 
            "CodebuildProject", 
            project_name="backstage-app-pipeline",
            build_spec=codebuild.BuildSpec.from_object(build_spec), # has to be compiled at deploy time rather than execution time.
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_4_0, privileged=True),
        )
        # add policy to update push to ECR
        policy =  iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
        build_project.role.add_managed_policy(policy)
        # add policy to access secret in build
        secrets_policy=iam.PolicyStatement(
            resources=[github_app_arn],
            actions=['secretsmanager:GetSecretValue'],
        )
        build_project.add_to_role_policy(secrets_policy)

        # code build action will use docker to build new image and push to ECR
        # the buildspec.yaml is in the backstage app repo
        repo_uri = crs.image_repo.repository_uri
        base_repo_uri = f"{props.get('AWS_ACCOUNT')}.dkr.ecr.{props.get('AWS_REGION')}.amazonaws.com"

        build_action = actions.CodeBuildAction(
            action_name="Docker-Build",
            project=build_project,
            input=self.source_output,
            outputs=[self.build_output],
            environment_variables={
                "BASE_REPO_URI" : codebuild.BuildEnvironmentVariable(value=base_repo_uri),
                "GITHUB_APP_ARN": codebuild.BuildEnvironmentVariable(value=github_app_arn),
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(value=repo_uri),
                "AWS_REGION": codebuild.BuildEnvironmentVariable(value=props.get("AWS_REGION")),
                "CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value=props.get("CONTAINER_NAME")),
                "DOCKERFILE": codebuild.BuildEnvironmentVariable(value=props.get("DOCKERFILE", "dockerfile")),
            },
        )

        # ECS deploy actions will take file made in build stage and update the service with new image

        self.pipeline = codepipeline.Pipeline(self, "backstagepipeline", cross_account_keys=False, pipeline_name="backstage-app-pipeline")

        self.pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        self.pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )
        if codestar_notify_arn is not None:
            # pull in existing slackbot channel integration
            slack_channel = chatbot.SlackChannelConfiguration.from_slack_channel_configuration_arn(self, 
                "SlackChatbot",
                slack_channel_configuration_arn=codestar_notify_arn,
            )
            pipe_exec_notify = self.pipeline.notify_on_execution_state_change("pipelinenotification", slack_channel)
            pipe_approval_notify = self.pipeline.notify_on_any_manual_approval_state_change("pipelineapproval", slack_channel)

    def add_deploy_stage( self, name: str, fargate_service: ecs.IBaseService, approval: bool = False, emails: list = []):
        dps = self.pipeline.add_stage(
            stage_name=name+"-deploy"
        )
        runorder =1
        if approval :
            dps.add_action(
                actions.ManualApprovalAction(action_name=name+"-stage-approval",notify_emails=emails, run_order=runorder)
            )
            runorder+=1
        dps.add_action(
            actions.EcsDeployAction(
                    service=fargate_service,
                    action_name=name+"-deploy",
                    input=self.build_output,
                    run_order=runorder
                )
        )
