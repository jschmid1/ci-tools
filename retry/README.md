# GitHub CI Monitor

This Python script monitors the Continuous Integration (CI) status of a specific pull request in a GitHub repository. The pull request is specified by passing the URL as a command-line argument.

## main.py

The `main.py` script performs the following tasks:

1. Authenticates to GitHub using a token.
2. Retrieves a specific repository and pull request from the provided URL.
3. Checks the CI status of the latest commit in the pull request.
4. If the CI is still running, it waits and then checks again.
5. If the CI has completed and is successful, it exits.
6. If the CI has completed and has failures, it attempts to restart the failing checks.
7. If the maximum number of retries is reached, it exits with an error.

## Environment Variables

The script requires the following environment variables:

- `GITHUB_TOKEN`: Your GitHub token.
- `RETRY_CI_LOG_LEVEL`: The log level (default is "INFO").

## Dependencies

This script has one dependency to the PyGithub library. You can install it by using the requirements file

```bash
pip3 install -r .requirements
```

## Running the Script

To run the script, use the following command:

```bash
python main.py <GitHub PR URL>
```

## Examples

```bash
export GITHUB_TOKEN=my-secret-token
export RETRY_CI_LOG_LEVEL=debug
python3 main.py https://github.com/jschmid1/ci-tools/pulls/1
```
