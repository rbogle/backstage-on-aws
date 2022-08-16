# Backstage Infrastructure Stack
The infrastructure stack to host backstage consists of:

- ECS Fargate cluster
- ECS Service definition
- ECS Task definitions for each stage (Test, Prod)
- Aurora postgresql dbs for each stage (Test, Prod)
- Public and Private subnets on a dedicated VPC
- Elastic Load Balancers for each stage (Test, Prod)
- ACM Certs for each stage (Test, Prod)
- Application Pipeline to build and deploy the application code in a container 

This stack is created and deployed by the infrastructure pipeline.

Multiple stages can be added by adding more stages to the `env-config.yaml` file. 
