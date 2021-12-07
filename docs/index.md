# Backstage Infrastructure
This project uses [CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy a containerized version of [Backstage](https://backstage.io) running in AWS ECS Fargate with AWS Aurora Postgres, along with all the other required supporting infrastructure. This enables a serverless deployment of your Backstage application. This CDK project creates two independent stacks which create or deploy CI/CD pipelines, supporting application infrastructure, and app containers to AWS. The combination of pipelines, multiple environments, and cdk enables a continuous deployment workflow with release on demand capabilities. The two stacks each have important roles:

## The backstage stack and pipeline
This stack creates multiple environments within a ECS Fargate cluster along with multiple Aurora postgres dbs for persistence, and puts those behind application load balancers each with a custom domain name. 
Additionally it builds a codepipeline called the `backstage-app-pipline` which builds and deploys a new application image based on commits in a repo where the backstage app code resides via an ECS deployment event. Once this cdk stack is deployed, you only need to update your backstage application code to update the current running application. By using multiple stages, you are able to test your new changes before manually promoting to the production environment.

## The infrastructure pipeline
The infra pipeline stack creates a codepipeline to both update itself and to deploy the backstage stack described above. This set of infrastructure code is self-updating and self-healing, and requires no manual intervention after the initial manual deployment of the infra-pipeline stack.

## Diagram
![Image of Architecture](./assets/arch.png)

## Documentation

- [Pipelines Descriptions](./pipelines.md)
- [Application Infrstructure](./stack.md)
- [Settings and Configuration](./settings.md)
- [Bootstrap the Stacks](./bootstrap.md)
- [Deployment](./deploy.md)
