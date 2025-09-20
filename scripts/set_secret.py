import sys
import getpass
import os

# Add the project root to the path to allow importing the framework
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ucore_framework.core.resource.secrets import EnhancedSecretsManager

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/set_secret.py <secret_name>")
        sys.exit(1)

    secret_name = sys.argv[1]
    secret_value = getpass.getpass(f"Enter value for secret '{secret_name}': ")

    if not secret_value:
        print("Error: Secret value cannot be empty.")
        sys.exit(1)

    manager = EnhancedSecretsManager()
    manager.set_secret(secret_name, secret_value)
    print(f"Secret '{secret_name}' has been securely stored.")

if __name__ == "__main__":
    main()

# Example usage:
#   python scripts/set_secret.py ucore_app_secret_key
