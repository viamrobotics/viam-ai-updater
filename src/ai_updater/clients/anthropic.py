from pathlib import Path
import json
from typing import List, Dict

from .base import Client
import anthropic

class Antrhopic(Client):

    client: anthropic.Client

    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_tree(self, path: Path | str, max_depth: int = 5) -> str:
        root = Path(path)
        if not root.exists():
            return f"Error: Path '{root}' does not exist."
        if not root.is_dir():
            return f"Error: Path '{root}' is not a directory."

        tree_str = [f"{root.name}/"]
        
        def _add_to_tree(current_path: Path, prefix: str, current_depth: int):
            if max_depth is not None and current_depth >= max_depth:
                return

            try:
                # Get all items
                all_paths = list(current_path.iterdir())
                
                # FILTER: Exclude hidden files (starts with .) and __pycache__
                filtered_paths = [
                    p for p in all_paths
                    if not p.name.startswith(".") and p.name != "__pycache__"
                ]

                # Sort: Directories first, then alphabetical
                paths = sorted(
                    filtered_paths,
                    key=lambda p: (not p.is_dir(), p.name.lower())
                )
                
            except PermissionError:
                tree_str.append(f"{prefix}└── [Permission Denied]")
                return

            # Calculate pointers for the tree structure
            pointers = [("├── ", "│   ")] * (len(paths) - 1) + [("└── ", "    ")]

            for pointer, path in zip(pointers, paths):
                connector, sub_prefix = pointer
                entry_name = f"{path.name}/" if path.is_dir() else path.name
                tree_str.append(f"{prefix}{connector}{entry_name}")

                if path.is_dir():
                    _add_to_tree(path, prefix + sub_prefix, current_depth + 1)

        _add_to_tree(root, "", 0)
        return "\n".join(tree_str)

    
    def get_example_files(self, sdk_path: Path | str) -> str:
        """Load key example files that demonstrate SDK patterns."""
        
        sdk_path = Path(sdk_path)
        
        examples = []
        
        # Define patterns for important files to include as examples
        example_patterns = [
            "**/components/arm/arm.py",         # Component base class
            "**/components/arm/client.py",      # Component gRPC client
            "**/components/arm/service.py",     # Component gRPC service
            "**/services/motion/motion.py",     # Service base class
            "**/services/motion/client.py",     # Service gRPC client
            "**/services/motion/service.py",    # Service gRPC service
            "**/app/app_client.py",             # App client
        ]
        
        for pattern in example_patterns:
            for file_path in sdk_path.glob(pattern):
                rel_path = file_path.relative_to(sdk_path)
                content = file_path.read_text()
                examples.append(f"# File: {rel_path}\n```python\n{content}\n```")
        
        return "\n\n".join(examples)
    
    def analyze_protobuf_changes(self, generated_path: Path) -> Dict:
        """
        Analyze the generated protobuf Python files to understand what changed.
        Returns services, messages, and RPCs that were added/modified.
        """
        changes = {
            "services": [],
            "messages": [],
            "rpcs": {}
        }
        
        # Parse generated *_pb2_grpc.py files for services
        for grpc_file in generated_path.rglob("*_pb2_grpc.py"):
            content = grpc_file.read_text()
            
            # Extract service names (look for class XXXServicer)
            import re
            servicers = re.findall(r'class (\w+)Servicer\(', content)
            for servicer in servicers:
                service_name = servicer.replace('Servicer', '')
                changes["services"].append(service_name)
                
                # Extract RPC methods for this service
                # Look for method definitions in the servicer
                methods = re.findall(r'def (\w+)\(self, request, context\)', content)
                changes["rpcs"][service_name] = methods
        
        # Parse *_pb2.py files for messages
        for pb2_file in generated_path.rglob("*_pb2.py"):
            content = pb2_file.read_text()
            
            # Extract message class names
            import re
            messages = re.findall(r'class (\w+)\(_message\.Message\)', content)
            changes["messages"].extend(messages)
        
        return changes
    
    def find_relevant_files(self, sdk_path: Path, protobuf_changes: Dict) -> List[Dict]:
        """
        Find SDK files that wrap the changed protobuf services/messages.
        Returns list of dicts with file path and content.
        """
        relevant_files = []
        
        # Get all service and message names
        entities = set()
        entities.update(s.lower() for s in protobuf_changes.get("services", []))
        entities.update(m.lower() for m in protobuf_changes.get("messages", []))
        
        # Find SDK wrapper files (not the generated _pb2 files)
        for py_file in sdk_path.rglob("*.py"):
            # Skip generated protobuf files
            if py_file.name.endswith('_pb2.py') or py_file.name.endswith('_pb2_grpc.py'):
                continue
            if py_file.name.startswith('test_'):
                continue
            
            content = py_file.read_text().lower()
            if any(entity in content for entity in entities):
                rel_path = py_file.relative_to(sdk_path)
                file_content = py_file.read_text()
                relevant_files.append({
                    "path": str(rel_path),
                    "content": file_content
                })
        
        return relevant_files
    
    def load_sdk_metadata(self, sdk_path: Path) -> Dict[str, str]:
        """Load SDK metadata like README, architecture docs, etc."""
        metadata = {}
        
        # Load README if exists
        for readme in ['README.md', 'README.rst', 'ARCHITECTURE.md']:
            readme_path = sdk_path / readme
            if readme_path.exists():
                metadata[readme] = readme_path.read_text()
        
        # Load style guide if exists
        style_guide_path = sdk_path / 'STYLE_GUIDE.md'
        if style_guide_path.exists():
            metadata['STYLE_GUIDE.md'] = style_guide_path.read_text()
        
        return metadata
        
    def generate_sdk_updates(
        self,
        protobuf_diff: str,
        sdk_path: str,
        generated_path: str,
        target_language: str = "python",
        force_full_context: bool = False
    ) -> Dict:
        """
        Generate SDK updates based on protobuf changes.
        
        Args:
            protobuf_diff: The git diff of generated protobuf binding files
            sdk_path: Path to the SDK directory (your hand-written wrappers)
            generated_path: Path to generated protobuf files (*_pb2.py, *_pb2_grpc.py)
            target_language: Target language for SDK generation
            force_full_context: If True, include all SDK files (expensive)
        """
        sdk_path = Path(sdk_path)
        generated_path = Path(generated_path)
        
        # Gather SDK information
        directory_tree = self.generate_tree(sdk_path)
        example_files = self.get_example_files(sdk_path)
        metadata = self.load_sdk_metadata(sdk_path)
        
        # Analyze what changed in the generated protobuf files
        protobuf_changes = self.analyze_protobuf_changes(generated_path)
        
        # Find SDK wrapper files that likely need updates
        relevant_files = self.find_relevant_files(sdk_path, protobuf_changes)
        
        # Build STATIC system prompt (this should be identical across runs for caching)
        static_system_prompt = f"""You are an expert SDK generator for {target_language}. Your job is to analyze protobuf API changes and generate corresponding updates to SDKs.

CRITICAL RULES - PRESERVE EXISTING CODE:
1. NEVER delete existing code unless explicitly instructed
2. ONLY add new methods/classes for new protobuf services/messages
3. ONLY modify existing methods if the protobuf signature changed
4. Preserve all existing functionality, comments, and structure
5. When in doubt, ADD rather than REPLACE

Key Responsibilities:
1. Parse the protobuf diff to identify added/modified/removed fields, methods, and services
2. Generate idiomatic {target_language} code that matches existing patterns
3. Maintain consistency with the SDK's architecture
4. Add appropriate error handling, type hints, and documentation
5. Generate corresponding tests

Output Format:
Return a JSON object with this structure:
{{
  "analysis": "Detailed summary of protobuf changes and their implications",
  "affected_services": ["list", "of", "services"],
  "changes_needed": [
    {{
      "file": "relative/path/to/file.py",
      "action": "create|modify|add_method",
      "reason": "Why this change is needed",
      "modification_type": "append|insert_after|replace_function",
      "target_location": "class_name or function_name if modifying",
      "code": "The code to add (not the entire file unless creating new file)"
    }}
  ],
  "tests_needed": [
    {{
      "file": "relative/path/to/test_file.py",
      "description": "What this test validates",
      "code": "Complete test code"
    }}
  ],
  "warnings": ["Any potential issues or manual review needed"]
}}"""

        # STATIC cached block 1: Base instructions
        system_blocks = [
            {
                "type": "text",
                "text": static_system_prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        # STATIC cached block 2: Example files (these don't change often)
        example_files_block = f"""# Example SDK Files

These files demonstrate the patterns and conventions used in this SDK:

{example_files}

Follow these patterns when generating new code. When modifying existing files, maintain the same style and structure."""

        system_blocks.append({
            "type": "text",
            "text": example_files_block,
            "cache_control": {"type": "ephemeral"}
        })
        
        # STATIC cached block 3: Style guide
        style_guide_text = metadata.get('STYLE_GUIDE.md', 'Follow Python PEP 8 conventions.')
        system_blocks.append({
            "type": "text",
            "text": f"""# Style Guide

{style_guide_text}""",
            "cache_control": {"type": "ephemeral"}
        })
        
        # STATIC cached block 4: Architecture overview
        architecture_text = f"""# SDK Directory Structure

```
{directory_tree}
```

# Architecture Overview

{metadata.get('README.md', 'No README found')}

{metadata.get('ARCHITECTURE.md', '')}"""

        system_blocks.append({
            "type": "text",
            "text": architecture_text,
            "cache_control": {"type": "ephemeral"}
        })
        
        # Build DYNAMIC user message (changes each run, NOT cached)
        user_message = f"""Analyze the provided git diff to understand what changes have been made to the proto definitions.

```diff
{protobuf_diff}
```

# Your Task
Generate INCREMENTAL updates to wrap these protobuf bindings. For each change:
1. Specify exactly which file to modify and where to add code
2. Provide ONLY the new code to add, not the entire file
3. For new services: Create new wrapper classes
4. For existing services: Add new methods or modify existing ones
5. NEVER delete or replace existing code unless the protobuf definition was removed

Remember: The goal is to ADD new functionality or UPDATE existing functionality, not rewrite the SDK."""
        
        print(f"Sending request to Claude with {len(system_blocks)} cached blocks...")
        print(f"Relevant files found: {len(relevant_files)}")
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000
            },
            system=system_blocks,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Parse response
        result = {
            "thinking": None,
            "response": None,
            "usage": response.usage
        }

        for block in response.content:
            if block.type == "thinking":
                result["thinking"] = block.thinking
            elif block.type == "text":
                text = block.text
                
                # Try multiple approaches to extract JSON
                try:
                    # First, try to find JSON within markdown code blocks
                    if "```json" in text or "```" in text:
                        # Extract content between code fences
                        import re
                        json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
                        if json_match:
                            text = json_match.group(1)
                    
                    # Try to parse as JSON
                    result["response"] = json.loads(text.strip())
                except json.JSONDecodeError:
                    # If that fails, try to find JSON object in the text
                    try:
                        import re
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            result["response"] = json.loads(json_match.group(0))
                        else:
                            result["response"] = {"raw": text}
                    except (json.JSONDecodeError, AttributeError):
                        result["response"] = {"raw": text}
        
        return result
        
        for block in response.content:
            if block.type == "thinking":
                result["thinking"] = block.thinking
            elif block.type == "text":
                text = block.text
                try:
                    # Remove markdown code fences if present
                    if text.strip().startswith("```"):
                        lines = text.strip().split('\n')
                        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
                    result["response"] = json.loads(text.strip())
                except json.JSONDecodeError:
                    result["response"] = {"raw": text}
        
        return result

    def apply_changes(self, changes: List[Dict], sdk_path: Path, dry_run: bool = True):
        """Apply the generated changes to the SDK."""
        for change in changes:
            file_path = sdk_path / change['file']
            
            print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {change['file']}")
            print(f"  Action: {change['action']}")
            print(f"  Reason: {change['reason']}")
            
            if change['action'] == 'create':
                print(f"  → Creating new file")
                if not dry_run:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(change['code'])
                    print(f"  ✓ Created {file_path}")
            
            elif change['action'] == 'add_method':
                print(f"  → Adding method to existing file")
                if not dry_run:
                    if file_path.exists():
                        existing_content = file_path.read_text()
                        # Simple append - in production you'd want smarter insertion
                        new_content = existing_content.rstrip() + "\n\n" + change['code']
                        file_path.write_text(new_content)
                        print(f"  ✓ Added method to {file_path}")
                    else:
                        print(f"  ⚠ File doesn't exist, creating new file")
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(change['code'])
            
            elif change['action'] == 'modify':
                print(f"  → Modifying {change.get('target_location', 'file')}")
                if not dry_run:
                    # In production, you'd use AST manipulation to precisely modify
                    # For now, show a warning that manual review is needed
                    print(f"  ⚠ MANUAL REVIEW NEEDED - modification requires careful merging")
                    print(f"  Code to integrate:\n{change['code'][:200]}...")


    def main(self, sdk_root: str):
        """Example workflow usage."""        
        # Example paths - adjust to your repo structure
        sdk_path = f"{sdk_root}/src"              # Your hand-written SDK wrappers
        generated_path = f"{sdk_path}/viam/gen"  # Generated *_pb2.py files
        diff_path = f"{sdk_root}/protobuf_bindings.diff"     # Diff of generated files
        
        # Load the protobuf bindings diff
        protobuf_diff = Path(diff_path).read_text()
        
        print("=" * 80)
        print("SDK Auto-Update Workflow")
        print("=" * 80)
        print(f"SDK Path: {sdk_path}")
        print(f"Generated Protobuf Path: {generated_path}")
        print(f"Diff: {diff_path}")
        
        # First run
        print("\n=== FIRST RUN (will create cache) ===")
        result1 = self.generate_sdk_updates(
            protobuf_diff=protobuf_diff,
            sdk_path=sdk_path,
            generated_path=generated_path,
            target_language="python"
        )
        
        print(f"\n=== First Run Usage Stats ===")
        print(f"Input tokens:          {result1['usage'].input_tokens:,}")
        print(f"Cache creation tokens: {result1['usage'].cache_creation_input_tokens:,}")
        print(f"Cache read tokens:     {result1['usage'].cache_read_input_tokens:,}")
        print(f"Output tokens:         {result1['usage'].output_tokens:,}")
    
        # Show analysis
        response = result1['response']
        if isinstance(response, dict):
            print(response.keys())
            if 'analysis' in response:
                print(f"\n{'=' * 80}")
                print("Analysis")
                print("=" * 80)
                print(response['analysis'])
                
                print(f"\n{'=' * 80}")
                print(f"Changes Required ({len(response['changes_needed'])} modifications)")
                print("=" * 80)
                
                # Apply changes (dry run by default)
                self.apply_changes(response['changes_needed'], Path(sdk_path), dry_run=False)
                
                if response.get('warnings'):
                    print(f"\n{'=' * 80}")
                    print("⚠️  Warnings")
                    print("=" * 80)
                    for warning in response['warnings']:
                        print(f"  • {warning}")

    async def run(self, sdk_root:str, **kwargs):
        self.main(sdk_root)
