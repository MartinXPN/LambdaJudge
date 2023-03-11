# <img alt="Profound Academy logo" src="https://i.imgur.com/Sf1Q7ro.png" width="80"/> LambdaJudge

Serverless Online Judge for automated solution checking written in Python.

![linting](https://github.com/MartinXPN/LambdaJudge/actions/workflows/pre-commit.yaml/badge.svg)
![unit-tests](https://github.com/MartinXPN/LambdaJudge/actions/workflows/unit-test.yaml/badge.svg)
![integration-tests](https://github.com/MartinXPN/LambdaJudge/actions/workflows/integration-test.yaml/badge.svg)


LambdaJudge compiles and executes code in several languages and returns the results stating if the code passed given tests or resulted in an error.
The judge supports several languages including `C++`, `Python3`, `C#`, `JavaScript (Node.js)`.
The whole execution happens in an AWS Lambda which does not have internet access (is in a VPC inside a private subnet) and does not have access outside the container.
All the test cases are encrypted and the executor process does not have the key.
Therefore, the arbitrary code cannot read the answers for the test cases.
The test cases are kept on EFS (Elastic File System), which is mounted with a read access.

# Infrastructure
LambdaJudge infrastructure is best described in the image below.

### Checkers and CodeRunners
* A submission comes through an API gateway, which triggers Bouncer Lambda.
Bouncer is not in a VPC, and therefore easily fetches the encryption key from the Secrets Manager.
* Afterward, it triggers the appropriate Lambda specific to the language of submission.
* The CodeRunner lambda gets the encrypted test cases from the attached EFS mounted in `read` mode.
* It then decrypts the contents of the appropriate problem test files and keeps the contents in memory.
* It then starts a new subprocess for each test case and passes the inputs as `stdin`.
* After reading the outputs from `stdout` it passes those to the checker.
* *Note that the submitted code does not have access to the encryption key, therefore is not able to decrypt the contents of EFS

### Sync EFS with S3
* Instructors can upload problems to S3 and a separate Lambda function is responsible for syncing S3 with EFS
* A function is triggered on S3 upload, it gets the encryption key from the secrets manager and passes the path to S3 and the key to the `SyncS3WithEFS` lambda
* The syncing lambda which is in a VPC downloads the file from S3, unzips it, creates a json from the files inside, gzipps it and saves to EFS


[//]: # (created with https://app.creately.com/)
![LambdaJudge Infrastructure](https://i.imgur.com/AuVHUrq.png)

# Development

This project uses [AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
to define the serverless architecture and deploy it.
The serverless infrastructure is defined in `template.yaml`.
SAM default configs are defined in `samconfig.toml`.

In case of using IDEs, the AWS Toolkit plugin can speed up the process of working with SAM.
Here is the list of plugins for each IDE:
[CLion](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[GoLand](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[WebStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[Rider](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[PhpStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[RubyMine](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[DataGrip](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
[VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
[Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html).

### Prerequisites:
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* [pre-commit installed](https://pre-commit.com/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
* `pip install -r tests/requirements.txt` to run tests


### Running the project (need to have docker up and running):
```shell
sam build --use-container                                         # Builds the project
sam local invoke <FunctionName> --event events/pythonEcho.json    # Invokes the lambda function locally
sam local start-api && curl http://localhost:3000/                # Start and invoke API endpoints locally
sam local start-lambda                                            # Start all the functions (you can invoke them with boto3, have a look at integration tests)
sam deploy --guided                                               # Deploy the serverless application
sam logs -n <FunctionName> --tail                                 # Print log tail for the deployed function

pre-commit run --all-files                                        # Tidy-up the files before committing
```

### Running tests (coverage is not reported for integration tests)
```shell
sam build --use-container                                         # Builds the project
sam local start-lambda                                            # Start all the functions locally
pytest --cov=sync --cov=coderunners --cov=bouncer --cov-report term-missing
```

### Project structure
```markdown
LambdaJudge
|-> bouncer (forward the request to coderunners in VPC with a private Subnet)
|-> coderunners (are in a VPC with a private Subnet - execute code in different languages)
|-> sync (Lambda function that syncs S3 with EFS in a VPC)
|-> tests (include integration and unit tests)
|
|-> samconfig.toml (includes the default configurations for SAM CLI)
|-> template.yaml (defines the whole serverless infrastructure as a yaml file)
```
