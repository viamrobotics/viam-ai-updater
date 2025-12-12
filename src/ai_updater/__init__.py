import argparse
import asyncio
import os

from ai_updater.clients.base import Client
from ai_updater.clients.google import Google as GoogleClient
from ai_updater.clients.anthropic import Antrhopic as AnthropicClient


def main():
    """Main entry point for the AI updater script."""
    parser = argparse.ArgumentParser(description="Viam SDK AI Updater")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to print various helpful files",
    )
    parser.add_argument("--noai", action="store_true", help="Disable AI (for testing)")
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Attempt to apply patches to existing files",
    )
    parser.add_argument(
        "--sdk",
        type=str,
        help="The SDK that is being updated (currently supports python, cpp, typescript, flutter)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test",
        type=str,
        help="Enable when running tests. Supply path to root directory of desired test repo",
    )
    group.add_argument(
        "--work",
        type=str,
        help="Enable when running in workflow. Supply path to root direcory repo to be updated",
    )

    args = parser.parse_args()

    API_KEY_VARS: dict[str, Client] = {
        "GOOGLE_API_KEY": GoogleClient,
        "ANTRHOPIC_API_KEY": AnthropicClient,
    }

    client: Client | None = None
    for env_var, ClientConstructor in API_KEY_VARS.items():
        key = os.getenv(env_var)
        if key:
            client = ClientConstructor(key)

    if not client:
        raise ValueError(
            f"Could not create AI client -- no valid API keys found. Please set one of the following environment variables: {','.join(API_KEY_VARS.keys())}"
        )

    sdk_root = args.sdk
    if not sdk_root:
        raise ValueError("Please provide the SDK root directory using the --sdk option")

    asyncio.run(client.run(sdk_root, debug=args.debug, noai=args.noai, patch=args.patch, test=args.test))


if __name__ == "__main__":
    main()
