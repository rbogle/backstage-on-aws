import json
import yaml
from aws_cdk import (
    core, 
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr_assets as assets,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_rds as rds,
    aws_ssm as ssm,
    aws_secretsmanager as secrets,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
)

class BackstageStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, props: dict,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # properties
        host_name = props.get("HOST_NAME", 'backstage')
        domain_name = props.get("DOMAIN_NAME", 'example.com')
        fqdn = f"{host_name}.{domain_name}"
        db_username = props.get("POSTGRES_USER", 'postgres')
        db_port = int(props.get("POSTGRES_PORT", 5432))
        container_port = props.get("CONTAINER_PORT", '7000')
        container_name = props.get("CONTAINER_NAME", 'backstage')
        backstage_dir = props.get("BACKSTAGE_DIR", './backstage')
        acm_arn = props.get("ACM_ARN", None)
        # github info for codepipeline
        github_repo = props.get("GITHUB_REPO")
        github_org = props.get("GITHUB_ORG")
        

        # secretmgr info for github token
        github_token_secret_name = props.get("GITHUB_TOKEN_SECRET_NAME")
        # secretmgr info for auth to github users
        github_auth_secret_name = props.get("GITHUB_AUTH_SECRET_NAME")
        # secretmgr info for auth to AWS for plugins
        aws_auth_secret_name = props.get("AWS_AUTH_SECRET_NAME")

        aws_auth_secret = secrets.Secret.from_secret_name(self, "aws-auth-secret", aws_auth_secret_name)
        github_auth_secret = secrets.Secret.from_secret_name(self, "github-auth-secret", github_auth_secret_name)
        github_token_secret = secrets.Secret.from_secret_name(self, "github-token-secret", github_token_secret_name)

        # load in our buildspec file and convert to dict
        # this way we maintain build file as separate from app code. 
        with open(r'./buildspec.yml') as file:
            build_spec = yaml.full_load(file)

        # hosted zone for ALB and Cert
        # hosted_zone = route53.PublicHostedZone(
        #     self, "HostedZone",
        #     zone_name=domain_name
        # )
        # we already have a domain registered and zone hosted in Route53
        # so we do a lookup
        hosted_zone = route53.HostedZone.from_lookup(
            self, "hostedzone",
            domain_name=domain_name
        )

        # Cert for HTTPS if you specify ACM_ARN in your .env file 
        # we will use a pre-existing cert, else we generate on on-the-fly
        # this one is generated on the fly
        if acm_arn is None:
            cert = acm.Certificate(self, "Certificate",
                domain_name=fqdn,
                validation=acm.CertificateValidation.from_dns(hosted_zone)
            )
        # this one pulls in a prexisiting
        else:
            cert = acm.Certificate.from_certificate_arn(self, 'Certificate', acm_arn)

        # generate the json string for the secret with the .env username set
        secret_string = secrets.SecretStringGenerator(
                secret_string_template=json.dumps({"username": db_username}),
                generate_string_key="password",
                exclude_punctuation=True,
                include_space=False,
            )

        # generate and store password and username
        aurora_creds = secrets.Secret(
            self, 'AuroraCredentialsSecret', 
            secret_name= "backstage-db-auth",
            generate_secret_string=secret_string
        )

        # replace the .env pg passwd and github tokens with the generated one
        props['POSTGRES_PASSWORD'] = aurora_creds.secret_value_from_json('password').to_string()
        
        # by default the ecs_pattern used below will setup a public and private set of subnets. 
        vpc = ec2.Vpc(
            self, 
            "ECS-VPC",
            max_azs=2,
        )

        # SubnetGroup uses the private subnets by default this is passed to the aurora cluster
        # we could set this to an Isolated group if we created those subnets and have aurora isolated
        db_subnet_group = rds.SubnetGroup(
            self, "rds-subnet-group",
            description="Private Subnets for ECS & Aurora",
            vpc=vpc
        )

        # Define SGs so Fargate and no-one else can talk to aurora securly
        fargate_sg = ec2.SecurityGroup(
            self, "fargate-sec-group", 
            security_group_name="FargateSecGroup",
            description="Security group for Fargate Task",
            vpc=vpc
        )

        aurora_sg = ec2.SecurityGroup(
            self, "aurora-sec-group",
            security_group_name="AuroraSecGroup",
            description='Security group for Aurora Db',
            vpc=vpc
        )

        # default egress rules are for any, so we just need an ingress rule
        # to allow fargate to reach the aurora cluster and protect its access from elsewhere
        aurora_sg.add_ingress_rule(peer=fargate_sg, connection=ec2.Port.tcp(db_port))

        aurora_instance = rds.InstanceProps(
            vpc=vpc,
            instance_type= ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM),
            vpc_subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[aurora_sg],   
        )

        aurora_pg = rds.DatabaseCluster(
            self, "Aurora-PG-Database",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_10_14),
            credentials=rds.Credentials.from_secret(aurora_creds), 
            instance_props= aurora_instance,
            #subnet_group=db_subnet_group,
        )

        # set envar for DB hostname as generated by CFN
        props['POSTGRES_HOST'] = aurora_pg.cluster_endpoint.hostname

        # Lets make ECR repository for docker images and push a build there:
        # by specifying a dockerimage asset
        docker_asset = assets.DockerImageAsset(
            self,
            "BackstageImage",
            directory=backstage_dir,
            repository_name=container_name
        )

        # Now make the ECS cluster, Task def, and Service
        ecs_cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # this builds the backstage container on deploy and pushes to ECR
        ecs_task_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image=ecs.ContainerImage.from_docker_image_asset(docker_asset), #.from_asset(directory=backstage_dir),
            container_port=int(container_port),
            environment = props, # pass in the env vars
            container_name=container_name,
            secrets={
                "GITHUB_TOKEN" : ecs.Secret.from_secrets_manager(github_token_secret, field='secret'),
                "AUTH_GITHUB_CLIENT_ID": ecs.Secret.from_secrets_manager(github_auth_secret, field='id'),
                "AUTH_GITHUB_CLIENT_SECRET": ecs.Secret.from_secrets_manager(github_auth_secret, field='secret'),
                "AWS_ACCESS_KEY_ID": ecs.Secret.from_secrets_manager(aws_auth_secret, field='id'),
                "AWS_ACCESS_KEY_SECRET": ecs.Secret.from_secrets_manager(aws_auth_secret, field='secret')
            }
        )
        ecs_task_options.execution_role

        # Easiest way to stand up mult-tier ECS app is with an ecs_pattern,  we are making it HTTPS
        # and accessible on a DNS name. We give ECS the Security Group for fargate
        ecs_stack = ecs_patterns.ApplicationLoadBalancedFargateService(self, "MyFargateService",
            cluster=ecs_cluster,        # Required
            cpu=512,                    # Default is 256
            desired_count=1,            # Default is 1
            memory_limit_mib=2048,      # Default is 512
            public_load_balancer=True, # Default is False
            security_groups=[fargate_sg], # put the task/cluster in the group we created
            task_image_options= ecs_task_options,
            certificate=cert, #specifiying the cert enables https
            redirect_http=True,
            domain_name = fqdn,
            domain_zone = hosted_zone,
            enable_ecs_managed_tags = True,
        )  

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