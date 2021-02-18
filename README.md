
# Welcome Backstage deploy on AWS ECS Fargate

## Basic Steps

* Check your Prerequisites
* Clone this Repo
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

## Clone this Rep

## Create or Link to a Backstage App
Build a backstage app with postgres using `npx @backstage\create-app`. into a `backstage` sub directory in this repo.  
If you do this and then want to commit changes to your backstage app along with this deployment / infrastructure code you should remove the `backstage` line from gitignore.
or
Create a symlink from `backstage` to a external directory containing the backstage app code. 

## Add Dockerfile and .docker ignore
Add a dockerfile to the backstage dir from [backstage docs](https://backstage.io/docs/getting-started/deployment-other#docker) 

## Configure Backstage to use Env vars
Configure your `app-config.yaml` and `app-config.production.yaml` files to use ENV vars for critical parameters and secrets

## Create .env file
Create a dotenv file `.env` in the root of this project with your secrets and parameters 

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
