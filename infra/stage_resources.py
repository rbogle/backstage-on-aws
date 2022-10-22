
import json
from aws_cdk import (
    core, 
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    aws_certificatemanager as acm,
    aws_route53 as route53,
)
from .common_resources import CommonResourceStack

class StageResourceStack(core.Construct):
    def __init__(self, scope: core.Construct, id: str, props: dict, crs: CommonResourceStack) -> None:
        super().__init__(scope, id)

       # properties
        host_name = props.get("HOST_NAME", 'backstage')
        domain_name = props.get("DOMAIN_NAME", 'example.com')
        fqdn = f"{host_name}.{domain_name}"
        acm_arn = props.get("ACM_ARN", None)
        container_port = props.get("CONTAINER_PORT", '7000')
        container_name = props.get("CONTAINER_NAME", 'backstage')
        db_username = props.get("POSTGRES_USER", 'postgres')

        self.secret_mapping = dict()
        # secretmgr info for github token
        github_token_secret_name = props.get("GITHUB_TOKEN_SECRET_NAME", None)
        # secretmgr info for auth to github users
        github_auth_secret_name = props.get("GITHUB_AUTH_SECRET_NAME", None)
        # secretmgr info for auth to AWS for plugins
        aws_auth_secret_name = props.get("AWS_AUTH_SECRET_NAME", None)

        # # There is some weirdness here on synth with jsii when casting happens 
        # # using secret_mapping['VAR']=object assignment throws a casting error on synth
        # # so we make this a direct mapping of str,obj with the update() method and the mapping works
        # retrieve secrets and add to mapping if the right ENV VARS exists

        if github_token_secret_name is not None:
            github_token_secret = secrets.Secret.from_secret_name_v2(self, "github-token-secret", github_token_secret_name)
            self.secret_mapping.update({'GITHUB_TOKEN': ecs.Secret.from_secrets_manager(github_token_secret, field='secret')})
        if github_auth_secret_name is not None:
            github_auth_secret = secrets.Secret.from_secret_name_v2(
                self, "github-auth-secret", github_auth_secret_name)
            self.secret_mapping.update({'AUTH_GITHUB_CLIENT_ID': ecs.Secret.from_secrets_manager(github_auth_secret, field='id')})
            self.secret_mapping.update({"AUTH_GITHUB_CLIENT_SECRET": ecs.Secret.from_secrets_manager(github_auth_secret, field='secret')})
        if aws_auth_secret_name is not None:
            aws_auth_secret = secrets.Secret.from_secret_name_v2(self, "aws-auth-secret", aws_auth_secret_name)
            self.secret_mapping.update({"AWS_ACCESS_KEY_ID": ecs.Secret.from_secrets_manager(aws_auth_secret, field='id')})
            self.secret_mapping.update({"AWS_ACCESS_KEY_SECRET": ecs.Secret.from_secrets_manager(aws_auth_secret, field='secret')})
            # this is a duplicate of above, used by the @roadiehq/aws-credentials-plugin
            self.secret_mapping.update({"AWS_SECRET_ACCESS_KEY": ecs.Secret.from_secrets_manager(aws_auth_secret, field='secret')})

        # hosted zone for ALB and Cert
        # if create_r53:
        #     self.hosted_zone = route53.PublicHostedZone(
        #         self, "HostedZone",
        #         zone_name=domain_name
        #     )
        # else:
        # we already have a domain registered and zone hosted in Route53
        # so we do a lookup
        self.hosted_zone = route53.HostedZone.from_lookup(
            self, "hostedzone",
            domain_name=domain_name
        )

        if self.hosted_zone is None:
            self.hosted_zone = route53.PublicHostedZone(
                self, "HostedZone",
                zone_name=domain_name
            )

        # Cert for HTTPS if you specify ACM_ARN in your .env file 
        # we will use a pre-existing cert, else we generate on on-the-fly
        # this one is generated on the fly
        if acm_arn is None:
            self.cert = acm.Certificate(self, "Certificate",
                domain_name=fqdn,
                validation=acm.CertificateValidation.from_dns(self.hosted_zone)
            )
        # this one pulls in a prexisiting
        else:
            self.cert = acm.Certificate.from_certificate_arn(self, 'Certificate', acm_arn)

        # generate the json string for the secret with the .env username set
        secret_string = secrets.SecretStringGenerator(
                secret_string_template=json.dumps({"username": db_username}),
                generate_string_key="password",
                exclude_punctuation=True,
                include_space=False,
            )

        # generate and store password and username
        self.aurora_creds = secrets.Secret(
            self, 'AuroraCredentialsSecret', 
            secret_name= f"{id}-backstage-db-auth",
            generate_secret_string=secret_string
        )

        # replace the .env pg passwd generated one to share between ECS and Aurora
        # props['POSTGRES_PASSWORD'] = aurora_creds.secret_value_from_json('password').to_string()
        self.secret_mapping.update({'POSTGRES_PASSWORD': ecs.Secret.from_secrets_manager(self.aurora_creds, field='password')})

        self.aurora_pg = rds.DatabaseCluster(
            self, "PGDatabase",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_10_14),
            credentials=rds.Credentials.from_secret(self.aurora_creds), 
            instance_props= crs.aurora_instance,
            #subnet_group=db_subnet_group,
        )

        # set envar for DB hostname as generated by CFN
        props['POSTGRES_HOST'] = self.aurora_pg.cluster_endpoint.hostname

        # this builds the backstage container on deploy and pushes to ECR
        self.ecs_task_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
            image = ecs.ContainerImage.from_ecr_repository(crs.image_repo),
            container_port=int(container_port),
            environment = props, # pass in the env vars
            container_name=container_name,
            secrets = self.secret_mapping,
            task_role = crs.task_role,
            enable_logging=False
        )

        # Easiest way to stand up mult-tier ECS app is with an ecs_pattern,  we are making it HTTPS
        # and accessible on a DNS name. We give ECS the Security Group for fargate
        self.ecs_stack = ecs_patterns.ApplicationLoadBalancedFargateService(self, "BackstageService",
            cluster=crs.ecs_cluster,        # Required
            cpu=512,                    # Default is 256
            desired_count=1,            # Default is 1
            memory_limit_mib=2048,      # Default is 512
            public_load_balancer=True, # Default is False
            security_groups=[crs.fargate_sg], # put the task/cluster in the group we created
            task_image_options= self.ecs_task_options,
            certificate=self.cert, #specifiying the cert enables https
            redirect_http=True,
            domain_name = fqdn,
            domain_zone = self.hosted_zone,
            enable_ecs_managed_tags = True,
        ) 