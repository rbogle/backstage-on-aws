# Backstage Infrastructure
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of the foundations backstage instance along with the required infrastructure in AWS, to host our own [Backstage](https://backstage.io) based service. It creates two independent stacks which deploys pipelines, infrastructure, and app image containers to AWS.  

## The backstage stack and pipeline
This stack creates multiple environments within a ECS Fargate cluster along with Aurora postgres dbs for persistence, and puts those behind application load balancers with a custom domain name.
Finally it builds a codepipeline called the `backstage-app-pipline` which builds and deploys a new container image based on commits in a repo where the backstage app code resides and triggers an ECS deployment update. Once this cdk stack is deployed, you only need to update your backstage application code to update the current running application. 

## The infrastructure pipeline
The infra pipeline stack creates a codepipeline to both update itself and to deploy the backstage stack described above. In this way this set of infrastructure code is self-updating and self-healing, and requires no manual intervention after the initial manual deployment of the infra-pipeline stack.

## Diagram
![Image of Architecture](./assets/arch.png)

## Documentation

- [Pipelines Descriptions](./pipelines.md)
- [Application Infrstructure](./stack.md)
- [Settings and Configuration](./settings.md)
- [Bootstrap the Stacks](./bootstrap.md)
- [Deployment](./deploy.md)
