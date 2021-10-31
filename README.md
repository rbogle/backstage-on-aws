# Backstage Infrastructure
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of your backstage instance along with the required infrastructure in into a AWS account, to host your own [Backstage](https://backstage.io) based service. It creates two independent stacks which deploy pipelines, infrastructure, and app image containers to AWS. 
It is assumed you have more than a passing familiarity with:
- CDK
- AWS
- Backstage
- Docker
- Python

> WARNING! Deploying these stacks to AWS will incur costs!

## Versions
If you are looking for the orgininal version of this cdk stack without the use of pipelines see the `original` branch in this repo. 

## Prerequisites
you will need to have at least the following installed and configured:
- python3
- aws cli
- aws cdk

and you will need to have your backstage application code in a separate repo from this one. 

## The backstage stack and pipeline
This stack creates multiple environments within a ECS Fargate cluster along with Aurora postgres dbs for persistence, and puts those behind application load balancers with a custom domain name.
Finally it builds a codepipeline called the `backstage-app-pipline` which builds and deploys a new container image based on commits to a separate `backstage` repo where the backstage app code resides and triggers an ECS deployment update. Once this cdk stack is deployed, you only need to update your backstage application code to update the current running application. 

## The infrastructure pipeline
The infra pipeline stack creates a codepipeline to both update itself and to deploy the backstage stack described above. In this way this set of infrastructure code is self-updating and self-healing, and requires no manual intervention after the initial manual deployment of the infra-pipeline stack.

## Diagram
![Image of Architecture](./docs/assets/arch.png)

## Documentation

- [Pipelines Descriptions](./docs/pipelines.md)
- [Application Infrstructure](./docs/stack.md)
- [Settings and Configuration](./docs/settings.md)
- [Bootstrap the Stacks](./docs/bootstrap.md)
- [Deployment](./docs/deploy.md)

## To Do
 - Move config file into cdk context
 - Create bootstrap scripts
 - Move app-buildspec.yml back to app repo?
 - Remove aws integration user and use an ECS role for AWS auth. 
 - add dynamic route53 domain creation in the backstage-stack.
 - Add creation of ECR repository to the backstage-stack.
 - add Code* notification and connection creation to backstage-stack. 