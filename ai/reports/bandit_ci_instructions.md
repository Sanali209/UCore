# Bandit Static Analysis for CI/CD

To automatically scan the UCore Framework for security issues on every code change, add the following steps to your CI pipeline (e.g., GitHub Actions, Jenkins):

## 1. Install Bandit

```bash
pip install bandit
```

## 2. Run the Scan

```bash
bandit -r ucore_framework/ -ll --exit-with-error
```

- `-r`: Recursively scan the directory.
- `-ll`: Only report medium and high-severity issues.
- `--exit-with-error`: Fail the build if any issues are found.

## Explanation

Add these steps to your CI configuration to ensure every pull request and commit is checked for common Python security vulnerabilities, such as hardcoded secrets, use of insecure functions, and unsafe imports. This helps prevent security issues from reaching production.
