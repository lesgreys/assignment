"""
Code Extractor Utility
Automatically extracts source code snippets from files based on line numbers.
"""

import os
import json
from pathlib import Path


def extract_code_lines(file_path: str, line_spec: str) -> str:
    """
    Extract specific lines from a file.

    Args:
        file_path: Path to the source file (relative to project root)
        line_spec: Line specification (e.g., "10-20" for range, "15" for single line)

    Returns:
        Extracted code as string
    """
    # Get project root
    project_root = Path(__file__).parent.parent.parent

    # Build full path
    full_path = project_root / file_path

    if not full_path.exists():
        return f"# File not found: {file_path}"

    try:
        with open(full_path, 'r') as f:
            lines = f.readlines()

        # Parse line spec
        if '-' in line_spec:
            # Range of lines
            start, end = line_spec.split('-')
            start_idx = int(start) - 1  # Convert to 0-indexed
            end_idx = int(end)
            extracted = lines[start_idx:end_idx]
        else:
            # Single line
            line_num = int(line_spec) - 1
            extracted = [lines[line_num]]

        # Return joined lines, preserving indentation
        return ''.join(extracted).rstrip()

    except Exception as e:
        return f"# Error extracting code: {str(e)}"


def extract_function_code(file_path: str, function_name: str) -> str:
    """
    Extract an entire function's code from a file.

    Args:
        file_path: Path to the source file
        function_name: Name of the function to extract

    Returns:
        Complete function code as string
    """
    project_root = Path(__file__).parent.parent.parent
    full_path = project_root / file_path

    if not full_path.exists():
        return f"# File not found: {file_path}"

    try:
        with open(full_path, 'r') as f:
            lines = f.readlines()

        # Find function definition
        func_start = None
        for i, line in enumerate(lines):
            if f"def {function_name}(" in line:
                func_start = i
                break

        if func_start is None:
            return f"# Function '{function_name}' not found in {file_path}"

        # Extract function (simple heuristic: until next function or class def at same indent level)
        base_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
        func_lines = [lines[func_start]]

        for i in range(func_start + 1, len(lines)):
            line = lines[i]

            # Stop if we hit another function/class at same or lower indent level
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and (line.strip().startswith('def ') or line.strip().startswith('class ')):
                    break

            func_lines.append(line)

        return ''.join(func_lines).rstrip()

    except Exception as e:
        return f"# Error extracting function: {str(e)}"


def load_metadata():
    """Load component metadata from JSON file."""
    metadata_path = Path(__file__).parent.parent / 'config' / 'component_metadata.json'

    with open(metadata_path, 'r') as f:
        return json.load(f)


def generate_info_content_entry(component_id: str, metadata: dict) -> dict:
    """
    Generate complete info content for a component from its metadata.

    Args:
        component_id: ID of the component
        metadata: Metadata dictionary for the component

    Returns:
        Dictionary with tooltip, title, formula, python_code, sql_code
    """
    entry = {
        'tooltip': metadata.get('tooltip', ''),
        'title': metadata.get('title', component_id.replace('_', ' ').title()),
        'formula': metadata.get('formula_description', ''),
        'python_code': '',
        'sql_code': ''
    }

    # Extract Python code
    source_file = metadata.get('source_file')
    if source_file:
        source_lines = metadata.get('source_lines')
        source_function = metadata.get('source_function')

        if source_lines:
            # Extract by line numbers
            code = extract_code_lines(source_file, source_lines)
            entry['python_code'] = f"# From: {source_file} (lines {source_lines})\n\n{code}"
        elif source_function:
            # Extract entire function
            code = extract_function_code(source_file, source_function)
            entry['python_code'] = f"# From: {source_file}\n\n{code}"

    # Extract SQL code
    sql_file = metadata.get('sql_file')
    if sql_file:
        sql_lines = metadata.get('sql_lines')
        if sql_lines:
            code = extract_code_lines(sql_file, sql_lines)
            entry['sql_code'] = code
        else:
            # Extract entire file
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / sql_file
            if full_path.exists():
                with open(full_path, 'r') as f:
                    entry['sql_code'] = f.read().strip()

    return entry


def generate_all_info_content():
    """
    Generate complete info_content.py from metadata.

    Returns:
        Dictionary mapping component IDs to info content
    """
    metadata = load_metadata()
    all_content = {}

    for page_id, page_components in metadata.items():
        # Skip metadata keys
        if page_id.startswith('_'):
            continue

        for component_id, component_meta in page_components.items():
            full_id = f"{page_id}_{component_id}"
            all_content[component_id] = generate_info_content_entry(component_id, component_meta)

    return all_content


if __name__ == '__main__':
    # Test extraction
    print("Testing code extraction...")

    metadata = load_metadata()

    # Test with executive_overview kpi_total_arr
    test_meta = metadata['executive_overview']['kpi_total_arr']
    entry = generate_info_content_entry('kpi_total_arr', test_meta)

    print("\n=== Generated Entry ===")
    print(f"Title: {entry['title']}")
    print(f"Tooltip: {entry['tooltip']}")
    print(f"\nPython Code Preview:")
    print(entry['python_code'][:200] + "..." if len(entry['python_code']) > 200 else entry['python_code'])
