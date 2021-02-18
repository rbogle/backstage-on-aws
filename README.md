
# Deploy Backstage on AWS ECS Fargate and Aurora Postgres
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of backstage along with the required infrastructure in AWS, to host your own [Backstage](https://backstage.io) service.

It deploys the container into an ECS Fargate cluster and uses an Aurora postgres db for persistence, and puts those behind a application load balancer with a custom domain name.

> Warning! Deploying this into your AWS account will incur costs! 

## Basic Steps

- [Deploy Backstage on AWS ECS Fargate and Aurora Postgres](#deploy-backstage-on-aws-ecs-fargate-and-aurora-postgres)
  - [Basic Steps](#basic-steps)
  - [Check your prerequisites](#check-your-prerequisites)
  - [Clone or Fork this Repo](#clone-or-fork-this-repo)
  - [Integrate, Link, or Reference to a Backstage App](#integrate-link-or-reference-to-a-backstage-app)
    - [Integrate](#integrate)
    - [Link](#link)
    - [Reference](#reference)
  - [Add Dockerfile and .dockerignore](#add-dockerfile-and-dockerignore)
  - [Configure Backstage to use Env vars](#configure-backstage-to-use-env-vars)
  - [Create .env file](#create-env-file)
    - [Postgres config](#postgres-config)
    - [Routing & Discovery](#routing--discovery)
    - [AWS Environment](#aws-environment)
  - [Create a Route53 publichostedzone](#create-a-route53-publichostedzone)
  - [Initialize CDK project](#initialize-cdk-project)

## Check your prerequisites
Install all the things

- docker
- node 
- yarn
- python
- aws cli
- aws cdk

## Clone or Fork this Repo
You know what to do! :)


## Integrate, Link, or Reference to a Backstage App
The CDK deployment needs to find the backstage app code and its dockerfile to build and push an image for deployment. It defaults to looking in `./backstage`. 

### Integrate
If you want to couple this with your custom backstage application you can create or move the backstage code here.

Either copy or build a backstage app with postgres using `npx @backstage\create-app` into a `./backstage` sub directory in this repo. See this [guide]() at Backstage.io.

If you do this and then want to commit changes to your backstage app along with this infrastructure code you will need to remove the `backstage` line from gitignore.  

### Link
Alternatively, you can keep these separate and create a symlink from `./backstage` to a external directory containing the backstage app code.  
```
# ln -s backstage ../my-backstage-app-path 
```

### Reference
Finally, if you set the env var `BACKSTAGE_DIR` to point to where your backstage app code lives, cdk will pick up that path.


## Add Dockerfile and .dockerignore
Add a dockerfile (and a `.dockerignore`) to the backstage dir as detailed from the [backstage deployment docs](https://backstage.io/docs/getting-started/deployment-other#docker) 


## Configure Backstage to use Env vars
Configure your `app-config.yaml` and `app-config.production.yaml` files to use ENV vars for critical parameters and secrets


## Create .env file
Create a dotenv file `.env` in the root of this project with your secrets and parameters to configure both the CDK deployment and to pass them to your backstage app container at runtime.
The essential variables to define are:

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
- ACM_ARN --> (Optional) no default if left empty will generate a new cert
- TAG_STACK_NAME --> (Optional) defaults to backstage
- TAG_STACK_AUTHOR --> (Optional) defaults to foo.bar@example.com
- BACKSTAGE_DIR --> (Optional) defaults to ./backstage

## Create a Route53 publichostedzone
The cdk stack assumes a pre-existing domain name and hosted zone in route53.

You can change this to generate one on the fly if the domain is registered with AWS already, however its just as easy to setup a new hosted zone via the console. see: [Route53 docs](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html)

## Initialize CDK project
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
Finally, assuming no errors from synth, and you have set your env vars, you can deploy:

```
$ cdk deploy
```

Enjoy!
