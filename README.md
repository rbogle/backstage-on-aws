
# Deploy Backstage on AWS ECS Fargate
This project uses [CDK]() to deploy a containerized version of backstage along with the required infrastructure in AWS, to host your own Backstage service.    
It deploys the container into an ECS Fargate cluster and uses an Aurora postgres db for persistence, and puts those behind a application load balancer with a custom domain name.

Warning! Deploying this into your AWS will incur costs! 

## Basic Steps

* Check your Prerequisites
* Clone/Fork this Repo
* Build a backstage app
* Create a dockerfile 
* Configure app to use ENV vars
* Create a dotenv file 
* Initialize the CDK project

## Check your prerequisites
Install all the things

* docker
* node 
* yarn
* python
* aws cli
* aws cdk

## Clone or Fork this Repo
You know what to do! :)


## Integrate, Link, or Reference to a Backstage App
The CDK deployment needs to find the backstage app code and its dockerfile to build and push an image for deployment.  
It defaults to looking in `./backstage`. 

### Integrate
If you want to couple this with your custom backstage application you can create or move the backstage code here.  
Either copy or build a backstage app with postgres using `npx @backstage\create-app` into a `./backstage` sub directory in this repo. See this [guide]() at Backstage.io.  
If you do this and then want to commit changes to your backstage app along with this infrastructure code you will need to remove the `backstage` line from gitignore.  

### Link
Alternatively, you can keep these separate and create a symlink from `backstage` to a external directory containing the backstage app code.  
```
# ln -s backstage ../my-backstage-app-path 
```

### Reference
Finally, if you set the env var `BACKSTAGE_DIR` to point to where your backstage app code lives, cdk will pick up that path.


## Add Dockerfile and .docker ignore
Add a dockerfile to the backstage dir from [backstage docs](https://backstage.io/docs/getting-started/deployment-other#docker) 


## Configure Backstage to use Env vars
Configure your `app-config.yaml` and `app-config.production.yaml` files to use ENV vars for critical parameters and secrets


## Create .env file
Create a dotenv file `.env` in the root of this project with your secrets and parameters to configure both the CDK deployment and to pass them to your backstage app container at runtime.
The essential variables to define are:

### Postgres config
* POSTGRES_PORT --> (Optional) defaults to 5432
* POSTGRES_DB --> (Optional) no default lets backstage define
* POSTGRES_USER --> defaults to 'postgres'

### Routing & Discovery
* HOST_NAME --> (Optional) defaults to backstage
* DOMAIN_NAME --> (Required) defaults to example.com
* CONTAINER_PORT --> (Optional) defaults to 7000

### AWS Environment
* AWS_REGION --> (Optional) defaults to 'us-east-1'
* AWS_ACCOUNT --> (Required) no default
* ACM_ARN --> (Optional) no default if left empty will generate a new cert
* TAG_STACK_NAME --> (Optional) defaults to backstage
* TAG_STACK_AUTHOR --> (Optional) defaults to foo.bar@example.com
* BACKSTAGE_DIR --> (Optional) defaults to ./backstage


## Initialize CDK project
This project is set up like a standard Python project.  The initialization
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

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
