# Settings and Configurations

## Create a env-config.yaml file
Create a yaml file `env-config.yaml` in the config directory of this project with your secrets names and parameters to configure both the CDK deployment and to pass them to your backstage app container at runtime. 
A full clean and separate replicaton of the stacks and pipelines can be deployed with a new configuration file, by changing out the name of the the configuration file in `app.py`. This allows us to do a pre-test of any major changes to infrastructure or deployment flow in another account. see: `env-config-test.yaml`

Below are the variables used by cdk, you may add any others to `env-config.yaml` that you want to pass to the backstage runtime as env variables.

The essential variables for CDK deployment to define are:

### Postgres config (Optional)
- POSTGRES_PORT --> (Optional) defaults to 5432
- POSTGRES_DB --> (Optional) no default lets backstage define
- POSTGRES_USER --> (Optional) defaults to 'postgres'
- POSTGRES_PASSWORD --> (Optional) Not needed, will get generated and over-written on the fly
- POSTGRES_HOST --> (Optional) Not needed, will get generated and over-written on the fly

### Routing & Discovery
- HOST_NAME --> (Required) defaults to backstage, must be unique for each stage
- DOMAIN_NAME --> (Required) defaults to example.com
- CONTAINER_PORT --> (Optional) defaults to 7000
- CONTAINER_NAME --> (Optional) defaults to 'Backstage'
- DOCKERFILE --> (Optional) defaults to 'dockerfile' 

### AWS Environment
- AWS_REGION --> (Optional) defaults to 'us-east-1'
- AWS_ACCOUNT --> (Required) no default
- ACM_ARN --> (Optional) no default, if left empty will generate a new cert
- ECR_REP_NAME --> (Optional) if not set cdk will create new repo with container name.
- TAG_STACK_NAME -> (Required) no default
- TAG_STACK_PRODUCT -> (Optional) defaults to "Dev-Portal"


### Github Repo Info for Pipeline
- GITHUB_APP_REPO --> (Required) the name of the repo where your backstage app code is kept, without the user or org
- GITHUB_INFRA_REPO --> (Required) the name of this repo
- GITHUB_ORG --> (Required) the user or org where the backstage app repo lives
- GITHUB_INFRA_BRANCH --> (Optional) defaults to "main"
- GITHUB_APP_BRANCH --> (Optional) defaults to "main"
- CODESTAR_CONN_ARN --> (Required) the bootstrapped codestar connection for the pipelines to use
- CODESTAR_NOTIFY_ARN --> (Optional) the codestar notification connection for chatbot ARN

### Secrets to retreive at runtime but keep hidden:
- AWS_AUTH_SECRET_NAME --> (Required) the name of the AWS Secretmanager Secret which contains key/secret for backstage to acces aws services
- GITHUB_AUTH_SECRET_NAME --> (Required per stage) the name of the AWS Secretmanager Secret which holds the oauth key/secret for backstage to auth against Github  
- GITHUB_APP_ARN --> (Required) secret arn for github-app file, used in the app-pipeline during container build. 
