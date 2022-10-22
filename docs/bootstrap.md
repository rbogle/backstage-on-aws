# Bootstrapping and Setup 
There is a bit of manual bootstrapping in the deployment account required for the pipelines and stacks to succeed. 
This maybe mitigated with some automation scripting and added features to the cdk stacks. 

## Table of Contents
  - [Create a Route53 hosted zones](#create-a-route53-hosted-zones)
  - [Create ACM certs (optional)](#create-acm-certs-optional)
  - [Create Github OAuth Tokens](#create-github-oauth-tokens)
  - [Create AWS integration User and Tokens](#create-aws-integration-user-and-tokens)
  - [Store a secrets in AWS Secrets Manager](#store-a-secrets-in-aws-secrets-manager)
  - [Store Github-App secrets file(s) in Secrets Manager.](#store-github-app-secrets-files-in-secrets-manager)
  - [Create ECR repositories](#create-ecr-repositories)
  - [Codestar Connections and Notifications](#codestar-connections-and-notifications)

## Create a Route53 hosted zones
The cdk stack assumes a pre-existing domain name and hosted zone in route53 for each stage.
You must create manually a subdomain for each of the stages specified in route53. The stack will then associate that domain name with the application load balancer for that particular stage.

## Create ACM certs (optional)
If the stack does not find `ACM_ARN` defined in either the common configuration or the stage configurations it will try to create an ACM with the domain name specified for the stage.

## Create Github OAuth Tokens
If you want to use Github auth as your backstage IDP, you will need to create an Oauth token to allow backstage to connect. This can only be done by an owner of the org, and is found under the org developer settings. Save the token id and secret for storage in AWS secrets manager. Each OAuth token depends on callbacks to the url for the application and so must be unique for each domain name of the application. So if you have multiple stages configured, you will need to create multiple OAuth applications and secrets. 

## Create AWS integration User and Tokens
The backstage app uses tokens for access to AWS services like techdocs as well as any aws based plugin, in theory it should be able to use the credentials attached to the ECS container via a role (similar to EC2 roles), but this is a recent development and hasnt been tested. Currently we use setting particular environment variables in the runtime environment of the container to give the sevice access to AWS resources. We created an integration user and group and attached policies to the group for that user. The access token and secret are stored in AWS Secrets Manager. 
The current polices allowed for the group we used are:
- ReadOnlyAccess

## Store a secrets in AWS Secrets Manager
To give the backstage services access to 3rd party apis securely, we bootstrap aws secrets manager with the tokens created above and extract them at deploy time to inject in the infrastructure as environment variables

You will want to add the tokens created for Github auth and AWS auth into secret manager. The cdk stack will lookup those secrets and create new env vars detailed below and inject them into the container at runtime as the following variables:

- AUTH_GITHUB_CLIENT_ID --> looks in the secret name stored in  `GITHUB_AUTH_SECRET_NAME` for a key name of 'id'
- AUTH_GITHUB_CLIENT_SECRET --> looks in the secret name stored in `GITHUB_AUTH_SECRET_NAME` for a key name of 'secret'
- AWS_ACCESS_KEY_ID --> looks in the secret name stored in `AWS_AUTH_SECRET_NAME` for a key name of 'id'
- AWS_ACCESS_KEY_SECRET --> looks in the secret name stored in `AWS_AUTH_SECRET_NAME` for a key name of 'secret'

So we need to create secrets in secret manager with the following fields
  - Key: 'id' 
    - Value: token id
  - Key: 'secret'
    - Value: token secret

Further because the test instance and prod instance each have unique domain names we need separate github auth secrets configured for each environment. 
See [env-config.yaml](../configs/env-config.yaml), for examples of the github auth for each stage.


## Store Github-App secrets file(s) in Secrets Manager. 
Instead of using personal access tokens for backstage access the github apis, we have configured the use of a github-app for each of the orgs in github that you want to connect to.  Use of these apps requires providing a crendential configuration file to backstage at run time. The file includes a full PEM certificate that makes it difficult to pass via environment variables, so we store the raw file in Secrets Manager ([see example](https://medium.com/@nilouferbustani/securing-ssh-private-keys-using-aws-secrets-manager-6d93537c1037)) retrieve the contents in the app pipeline and write that to a file which is copied into the image during build. The ARNs for those secrets are loaded from the `env-config.yaml` file. 

To create a new github-app you can use a utility in the backstage app with
```bash
yarn backstage-cli create-github-app <github-org>
```
some permissions will need to be updated in Github on the app for the backstage to be able to execute all its actions, you can find those permissions under settings > developer settings > github-app. The following permissions are currently set in both orgs:

- actions (r/w)
- administration (r/w)
- contents (r/w)
- issues (r/w)
- metadata (r)
- pages (r/w)
- pull-requests (r/w)
- workflows (r/w)
- members (r)
- email addresses (r)

## Create ECR repositories
The application pipeline will build and push to an ECR repository name in the `ECR_REPO_NAME` variable in `env-config.yaml`. The cdk stack will attempt to create this repo with the name set or with the `CONTAINER_NAME`. The app-pipeline will build the first image and push it succesfully, so you do not need to pre-build and pre-seed the repo with an image. 

## Codestar Connections and Notifications
Both pipelines use a codestar connection to authenticate to github to watch for changes, as well as a codestar notification to push notifcations to slack via the AWS Chatbot integration. 
Each of these need to be setup in advance, at the time CDK did not support creation of these. 
The configuration file just needs the arn of each to provide to CDK stacks.
