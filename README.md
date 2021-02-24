
<!-- omit in toc -->
# Deploy Backstage on AWS ECS Fargate and Aurora Postgres
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of backstage along with the required infrastructure in AWS, to host your own [Backstage](https://backstage.io) service.

It deploys the container into an ECS Fargate cluster and uses an Aurora postgres db for persistence, and puts those behind a application load balancer with a custom domain name.
Finally it builds a codepipeline/codebuild project which will build a new image from commit to second github repo where your backstage app code resides, and then deploys the new image to the ECS cluster. 

Once this cdk stack is deployed, you only need to update your backstage code to update the current running application. 

This project assumes you have more than a passing familiarity with Python, AWS, CDK, Docker, and Backstage.

> Warning! Deploying this into your AWS account will incur costs! 

<!-- omit in toc -->
## Basic Steps

- [Check your prerequisites](#check-your-prerequisites)
- [Clone or Fork this Repo](#clone-or-fork-this-repo)
- [Integrate, Link, or Reference to a Backstage App](#integrate-link-or-reference-to-a-backstage-app)
  - [Integrate](#integrate)
  - [Link](#link)
  - [Reference](#reference)
- [Add Dockerfile and .dockerignore](#add-dockerfile-and-dockerignore)
- [Configure Backstage to use Env vars](#configure-backstage-to-use-env-vars)
- [Create a Route53 publichostedzone](#create-a-route53-publichostedzone)
- [Store a github token in AWS Secrets Manager](#store-a-github-token-in-aws-secrets-manager)
- [Create .env file](#create-env-file)
  - [Postgres config](#postgres-config)
  - [Routing & Discovery](#routing--discovery)
  - [AWS Environment](#aws-environment)
  - [Github Token Info](#github-token-info)
- [Initialize and Deploy CDK project](#initialize-and-deploy-cdk-project)

## Check your prerequisites
Install all the things....

- docker
- node 
- yarn
- python3
- aws cli
- aws cdk

## Clone or Fork this Repo
You know what to do! :)


## Integrate, Link, or Reference to a Backstage App
The CDK deployment needs to find the backstage app code and its dockerfile to build and push an image for deployment. It defaults to looking locally in `./backstage`. There a several options acheiving this:

### Integrate
If you want to couple this cdk stack with your custom backstage application you can create or move your backstage code here.

Either copy or build a backstage app with postgres using `npx @backstage\create-app` into a `./backstage` sub directory in this repo. See this [guide](https://backstage.io/docs/getting-started/create-an-app) at [Backstage.io](https://backstage.io/).

> Note: If you do this and then want to commit changes to your backstage app along with this infrastructure code you will need to remove the `backstage` line from gitignore.  

### Link
Alternatively, you can keep these repos separate and create a symlink to `./backstage` from an external directory containing the backstage app code.  
```
# ln -s ../my-backstage-app-path backstage  
```

### Reference
Finally, if you set an env var `BACKSTAGE_DIR` to point to where your backstage app code lives, cdk deploy will pick up that path for the container build.


## Add Dockerfile and .dockerignore
Add a multi-stage dockerfile (and a `.dockerignore`) to the backstage dir as detailed from the [backstage docker deployment docs](https://backstage.io/docs/getting-started/deployment-docker#multistage-build) 


## Configure Backstage to use Env vars
Configure your `app-config.yaml` and `app-config.production.yaml` files to use ENV vars for critical parameters and secrets

## Create a Route53 publichostedzone
The cdk stack assumes a pre-existing domain name and hosted zone in route53.

You can change this to generate one on the fly if the domain is registered with AWS already, however its just as easy to setup a new hosted zone via the console. see: [Route53 docs](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html)

## Store a github token in AWS Secrets Manager
The codepipeline deployment needs to connect to the github repository where the backstage app code will live.
To give the service access to github securely, we prime aws secrets manager with the github token and extract it the deploy time for the infrastructure. 
This tutorial can show you how to store the token: [Securing Tokens in a serverless pipeline](https://eoins.medium.com/securing-github-tokens-in-a-serverless-codepipeline-dc3a24ddc356)

You could take this further and place all credentials/tokens in secrets manager and extract them at build time. 

## Create .env file
Create a dotenv file `.env` in the root of this project with your secrets and parameters to configure both the CDK deployment and to pass them to your backstage app container at runtime. Below are the variables used by cdk, add any others you want your backstage runtime to have. The essential variables for CDK deployment to define are:

### Postgres config
- POSTGRES_PORT --> (Optional) defaults to 5432
- POSTGRES_DB --> (Optional) no default lets backstage define
- POSTGRES_USER --> (Optional) defaults to 'postgres'
- POSTGRES_PASSWORD --> (Optional) Not needed, will get generated and over-written on the fly
- POSTGRES_HOST --> (Optional) Not needed, will get generated and over-written on the fly

### Routing & Discovery
- HOST_NAME --> (Optional) defaults to backstage
- DOMAIN_NAME --> (Required) defaults to example.com
- CONTAINER_PORT --> (Optional) defaults to 7000

### AWS Environment
- AWS_REGION --> (Optional) defaults to 'us-east-1'
- AWS_ACCOUNT --> (Required) no default
- ACM_ARN --> (Optional) no default, if left empty will generate a new cert
- TAG_STACK_NAME --> (Optional) defaults to backstage
- TAG_STACK_AUTHOR --> (Optional) defaults to foo.bar@example.com
- BACKSTAGE_DIR --> (Optional) defaults to ./backstage

### Github Token Info
- GITHUB_SECRET_NAME --> (Required) the secret manager secret name
- GITHUB_SECRET_KEY --> (Required) the key in the secret of which the value is the github token
- GITHUB_REPO --> (Required) the name of the repo where your backstage app code is kept, without the user or org
- GITHUB_ORG --> (Required) the user or org where the backstage app repo lives


## Initialize and Deploy CDK project
This project is set up like a standard Python CDK project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```
Finally, assuming no errors from synth, and you have set your env vars in a `.env` file, you can deploy:

```
$ cdk deploy
```

Enjoy!
