# viam-ai-updater
Current home for the Viam SDK AI Updater

## Project Overview

This repository houses an AI-powered updater for the Viam SDKs. Its primary purpose is to automatically analyze protobuf definition changes as a git diff and generate corresponding updates to the Viam SDK's code and tests (more functionality to come).

## GitHub Actions Workflow Usage

This repository includes a reusable GitHub Actions workflow (`.github/workflows/ai-updater.yml`) that can be called by other repositories (e.g., an SDK repository) to automate the AI update process.

### Workflow Trigger (`workflow_call`)

The workflow is triggered by `workflow_call` and expects the following inputs:

*   `target_branch` (required): The branch in the calling SDK repository that needs to be updated.
*   `sdk` (required): The language of the calling SDK repository that needs to be updated (currently supports `python`, `typescript`, `cpp`, `flutter`)

And the following secrets:

*   `GOOGLE_API_KEY`: A Google Generative AI API key.

### Example Calling Workflow (in the SDK Repository)

To call this workflow from another repository's workflow (e.g., `viam-python-sdk`):

```yaml
# .github/workflows/sdk-update-trigger.yml (in the SDK repository)
name: Trigger AI SDK Update

on:
  push:
    branches:
      - workflow/update-proto # Or any branch that triggers the update

jobs:
  call-ai-updater:
    runs-on: ubuntu-latest
    steps:
      - name: Call AI Updater Workflow
        uses: ggottlob/viam-ai-updater/.github/workflows/ai-updater.yml@main # Replace 'main' with your desired branch/tag
        with:
          target_branch: ${{ github.ref_name }} # Passes the current branch name of the SDK repo
        secrets:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```


## Local Development Setup

To set up your local development environment, follow these steps:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-org/viam-ai-updater.git
    cd viam-ai-updater
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python3 -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
    Your terminal prompt should now indicate that the virtual environment is active (e.g., `(.venv) your-username@your-machine viam-ai-updater %`).

4.  **Install Dependencies:**
    Install the required Python packages using `uv pip install -r requirements.txt` from the `requirements.txt` file.
    ```bash
    uv pip install -r requirements.txt
    ```

## Running the AI Updater Script

The `ai_updater.py` script can be run in two primary modes: for testing against a mock SDK or for actual updates within a GitHub Workflow (as shown above).

### Arguments

*   `--debug`: (Optional) Enable debug mode to print various helpful files and additional logging.
*   `--noai`: (Optional) Disable AI model calls (useful for testing the script's logic without incurring API costs).
*   `--patch`: (Optional) Attempt to apply changes as patches to existing files rather than regenerating the entire file. If patching fails, the file will be regenerated.
*   `--sdk <sdk_name>`: (Required) Specify the SDK that is being updated. Currently supports `python`, `cpp`, `typescript`, and `flutter`.
*   `--test <path_to_test_repo>`: (Mutually Exclusive with `--work`) Enable test mode. Supply the path to the root directory of the test repository.
*   `--work <path_to_sdk_repo>`: (Mutually Exclusive with `--test`) Enable workflow mode. Supply the path to the root directory of the SDK repository that is being updated.

### Example Usage (Local)

To run the AI updater locally for development or testing:

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate

# Example: Running against a local test scenario (replace 'path/to/scenario-1-repo' with your test data)
python ai_updater/ai_updater.py --debug --test /path/to/scenario-1-repo
```

## Running Tests

This repo comes with a testing suite containing various examples of past proto updates to the Python SDK so you can test how the AI would act in that scenario.
Tests are written using `pytest` and are located in the `ai_updater/tests/` directory.

### Running all tests with Pytest

From the project root, with your virtual environment activated:

```bash
source .venv/bin/activate
pytest ai_updater/tests/
```

### Running specific tests with Pytest

To run tests for a specific scenario (e.g., `scenario-1`), use the `-k` flag:

```bash
source .venv/bin/activate
pytest ai_updater/tests/test_ai_updater.py -k "scenario-1"
```

### Running tests as a standalone script (for quick debugging)

The `test_ai_updater.py` script can also be run directly. When executed this way, it will run all defined scenarios with the comparison step skipped. This is useful for quickly debugging the AI Updater's generation process.

From the project root, with your virtual environment activated:

```bash
source .venv/bin/activate
python ai_updater/tests/test_ai_updater.py
```
