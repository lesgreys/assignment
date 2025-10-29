#!/usr/bin/env python3
"""
Metadata Validation Script

Validates component_metadata.json for:
- Duplicate component IDs
- Required fields
- Valid file paths
- Proper JSON structure

Run before starting dashboard to catch configuration errors early.
"""

import json
import sys
from pathlib import Path
from collections import Counter


def validate_metadata():
    """Validate component metadata file."""

    metadata_path = Path(__file__).parent.parent / 'src' / 'config' / 'component_metadata.json'

    print("Validating Component Metadata")
    print("=" * 60)

    # Load metadata
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"✓ Loaded metadata from: {metadata_path.name}")
    except FileNotFoundError:
        print(f"✗ ERROR: File not found: {metadata_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ ERROR: Invalid JSON: {e}")
        return False

    # Extract all component IDs with their page locations
    all_ids = []
    total_components = 0
    page_counts = {}

    for page_id, components in metadata.items():
        if page_id.startswith('_'):  # Skip metadata keys
            continue

        if not isinstance(components, dict):
            print(f"✗ ERROR: Page '{page_id}' components is not a dict")
            return False

        page_counts[page_id] = len(components)
        total_components += len(components)

        for component_id in components.keys():
            all_ids.append((component_id, page_id))

    print(f"✓ Found {total_components} components across {len(page_counts)} pages")

    # Check for duplicate component IDs
    print("\nChecking for duplicate component IDs...")
    id_counts = Counter([id for id, _ in all_ids])
    duplicates = {id: count for id, count in id_counts.items() if count > 1}

    if duplicates:
        print("✗ VALIDATION FAILED - Duplicate component IDs found:\n")
        for id, count in duplicates.items():
            print(f"  {id} (appears {count} times):")
            for comp_id, page_id in all_ids:
                if comp_id == id:
                    print(f"    - {page_id}")
            print()
        return False

    print(f"✓ All {total_components} component IDs are unique")

    # Check required fields for each component
    print("\nChecking required fields...")
    required_fields = ['type', 'title', 'tooltip']
    missing_fields = []

    for page_id, components in metadata.items():
        if page_id.startswith('_'):
            continue

        for component_id, component in components.items():
            for field in required_fields:
                if field not in component:
                    missing_fields.append((page_id, component_id, field))

    if missing_fields:
        print("✗ VALIDATION FAILED - Missing required fields:\n")
        for page_id, component_id, field in missing_fields:
            print(f"  {page_id}.{component_id}: missing '{field}'")
        print()
        return False

    print(f"✓ All components have required fields: {', '.join(required_fields)}")

    # Check file paths (if specified)
    print("\nChecking source file paths...")
    project_root = Path(__file__).parent.parent
    invalid_paths = []

    for page_id, components in metadata.items():
        if page_id.startswith('_'):
            continue

        for component_id, component in components.items():
            # Check Python source files
            if 'source_file' in component and component['source_file']:
                file_path = project_root / component['source_file']
                if not file_path.exists():
                    invalid_paths.append((page_id, component_id, 'source_file', component['source_file']))

            # Check SQL files
            if 'sql_file' in component and component['sql_file']:
                file_path = project_root / component['sql_file']
                if not file_path.exists():
                    invalid_paths.append((page_id, component_id, 'sql_file', component['sql_file']))

    if invalid_paths:
        print("⚠ WARNING - Invalid file paths found:\n")
        for page_id, component_id, field, path in invalid_paths:
            print(f"  {page_id}.{component_id}.{field}: {path}")
        print("\n  (Components will work but won't have code snippets)")
    else:
        print("✓ All specified file paths are valid")

    # Summary
    print("\n" + "=" * 60)
    print("✅ VALIDATION PASSED\n")
    print("Summary:")
    print(f"  Total components: {total_components}")
    print(f"  Total pages: {len(page_counts)}")
    print(f"  All IDs unique: Yes")
    print(f"  Required fields: Complete")
    if invalid_paths:
        print(f"  Invalid paths: {len(invalid_paths)} (warnings)")

    print("\nComponent breakdown by page:")
    for page_id, count in sorted(page_counts.items()):
        print(f"  {page_id:25} {count:2} components")

    return True


if __name__ == '__main__':
    success = validate_metadata()
    sys.exit(0 if success else 1)
