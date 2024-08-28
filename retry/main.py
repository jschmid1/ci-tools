from github import Github
import time
import sys
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# load from env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LOG_LEVEL = os.getenv("RETRY_CI_LOG_LEVEL", "INFO")
MAX_RETRIES = 5
RETRY_DELAY = 60  # Delay between retries in seconds

assert GITHUB_TOKEN

# Check if URL is passed as command-line argument
if len(sys.argv) < 2:
    print("Please provide the GitHub PR URL as a command-line argument.")
    sys.exit(1)

# Parse the URL
GITHUB_URL = sys.argv[1]

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger.setLevel(LOG_LEVEL.upper())


def get_failing_check_suites(check_suits):
    """return the failing checks."""
    return [
        check_suit for check_suit in check_suits if check_suit.conclusion == "failure"
    ]


def restart_check_suite(check_suite):
    """Restart the check suite by triggering re-run."""
    logger.info(f"Restarting check suite: {check_suite._id}")
    return check_suite.rerequest()


def get_latest_commit_sha(pull_request):
    logger.info(f"Getting latest commit for PR #{pull_request.number} CI results")
    return [commit for commit in pull_request.get_commits()][-1]


def get_check_suites(commit):
    return commit.get_check_suites()


def is_ci_still_running(check_suites):
    statuses = [suite.status for suite in check_suites]
    logger.debug(f"CI statuses: {statuses}")
    return not all(status == "completed" for status in statuses)


def is_ci_success(check_suites):
    conclusions = [
        suite.conclusion
        for suite in check_suites
        if suite.conclusion not in [None, "skipped"]
    ]
    logger.debug(f"CI conclusions: {conclusions}")
    return all(conclusion == "success" for conclusion in conclusions)


def extract_repo_info(parsed_url):
    # Extract the repository owner, name and pull request number
    repo_owner, repo_name, _, pull_request_number = parsed_url.path.strip("/").split(
        "/"
    )[0:4]
    if not all([repo_owner, repo_name, pull_request_number]):
        raise ValueError("Invalid GitHub URL provided")
    return repo_owner, repo_name, pull_request_number


def monitor_pull_request():
    # authenticate to GitHub
    g = Github(GITHUB_TOKEN)

    parsed_url = urlparse(GITHUB_URL)
    repo_owner, repo_name, pull_request_number = extract_repo_info(parsed_url)

    # get the repository and pull request
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    pull_request = repo.get_pull(int(pull_request_number))
    retries = 0

    while retries < MAX_RETRIES:
        check_suites = get_check_suites(get_latest_commit_sha(pull_request))
        if is_ci_still_running(check_suites):
            logger.info("CI is still running. Please wait...")
            # Do not increase the try counter in this case
            time.sleep(RETRY_DELAY)
            continue
        if is_ci_success(check_suites):
            # ci is all-green, exit
            logger.info("CI is already successful. Exiting.")
            sys.exit(0)
        # ci has issues, try to restart the failing checks
        failing_check_suits = get_failing_check_suites(check_suites)
        for check_suite in failing_check_suits:
            # restart the check suite
            restart_check_suite(check_suite)
        retries += 1
        logger.info(f"Retry attempt {retries}/{MAX_RETRIES}")
        time.sleep(RETRY_DELAY)

    logger.info(f"Max retries exceeded ({MAX_RETRIES}). Exiting.")
    sys.exit(1)


if __name__ == "__main__":
    try:
        monitor_pull_request()
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
