import json
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
)

class BackstageStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, props: dict,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # properties
        host_name = props.get("HOST_NAME", 'backstage')
        domain_name = props.get("DOMAIN_NAME", 'example.com')
        db_username = props.get("POSTGRES_USER", 'postgres')
        db_port = int(props.get("POSTGRES_PORT", 5432))
        container_port = props.get("CONTAINER_PORT", '7000')
        backstage_dir = props.get("BACKSTAGE_DIR", './backstage')
        acm_arn = props.get("ACM_ARN", None)
        fqdn = f"{host_name}.{domain_name}"

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
            secret_name= "BackstageDBCredentials",
            generate_secret_string=secret_string
        )

        # replace the .env passwd with the generated one
        props['POSTGRES_PASSWORD'] = aurora_creds.secret_value_from_json('password').to_string()

        # For additional security you can configure a VPC with subnets of different types ex:
        # public for the ALB
        # private for the Fargate cluster
        # isolated for aurora db
        vpc = ec2.Vpc(
            self, 
            "ECS-VPC",
            max_azs=2,
            # subnet_configuration=[
            #     {'name': 'Backstage_public','subnet_type' : ec2.SubnetType.PUBLIC},
            #     {'name': 'Backstage_private', 'subnet_type': ec2.SubnetType.PRIVATE },
            #     {'name': 'Backstage_isolated', 'subnet_type': ec2.SubnetType.ISOLATED }               
            # ]
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
            repository_name="backstage"
        )

        # Now make the ECS cluster, Task def, and Service
        ecs_cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # ecs_task_def = ecs.FargateTaskDefinition(
        #     self,
        #     "backstageTask",
        #     cpu=512,
        #     memory_limit_mib=2048,
        # )

        # ecs_task_def.add_container()

        # this builds the backstage container on deploy and pushes to ECR
        ecs_task_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(docker_asset), #.from_asset(directory=backstage_dir),
                container_port=int(container_port),
                environment = props, # pass in the env vars
        )

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

