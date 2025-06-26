"""Prompt for generating function implementations."""

FUNCTION_GENERATOR_P1 = '''
You are an expert Python developer implementing components for the Viam robotics SDK. Your task is to apply specific code changes to existing files based on detailed instructions. You must maintain the exact original functionality and strict formatting of all existing code while integrating new or modified functionality.

You need to implement the following new functionality and changes:

{implementation_details}

I will now provide you with the *complete current contents* of the **existing files** that you need to modify. For **new files**, no content will be provided, and you will generate them from scratch. Your output for each file (whether existing or new) should be the *full, regenerated content* after applying only the necessary edits, strictly adhering to the implementation details provided.
'''

FUNCTION_GENERATOR_P2 = '''
Task: Regenerate the complete file contents for each file, incorporating only the necessary edits as described in the implementation details provided.

CRITICAL INSTRUCTIONS:
1.  **Strict Adherence to Implementation Details**: Your primary guide for making changes is the `implementation_details`. Implement *only* what is explicitly requested there.
2.  **Preserve Original Code (for existing files)**: If you are provided with existing file content, DO NOT modify any of that existing code unless it is directly specified in the `implementation_details`. The existing code provided to you must be reproduced exactly, including all comments, blank lines, and existing formatting. **For new files, generate the entire content from scratch.**
3.  **Absolute Formatting Preservation**: When generating the new file contents, you MUST preserve all original formatting, including newlines, indentation, and whitespace, exactly as it appears in the provided existing files. DO NOT reformat any part of the code that is not explicitly altered by the new implementation. Your output must be valid, correctly formatted Python code.

For each file that needs to be modified or created, provide its file path (so it can be reinserted into the existing codebase), followed by the newly generated, complete file contents. The file contents should be raw code, not wrapped in markdown or any other formatting beyond standard Python syntax.
'''
