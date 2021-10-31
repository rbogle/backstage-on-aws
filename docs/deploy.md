# Initialize and Deploy CDK project
This project is set up like a standard Python CDK project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
executable in your path with access to the `venv`
package. 

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```
Finally, assuming no errors from synth, you have credentials to deploy to the account you wish, and you have set your env vars in a `env-config.yaml` file, you can deploy the infrastructure pipeline. 

Note: the infrastructure pipeline will build itself, then the `backstage-infra` stack including the application pipeline. It wont be until the app pipeline completes its first pass that a running task will be available in Fargate. 

```
$ cdk deploy backstage-infra-pipeline
```
Now sit back, grab some coffee, and watch Cloudformation and codepipeline work as your infrastructure and backstage app come to life!

Enjoy!