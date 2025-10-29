"""
Auto-generate info_content.py from component_metadata.json
Run this script whenever you update metadata to regenerate the info content file.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.code_extractor import generate_all_info_content, load_metadata
from utils.formula_formatter import create_formula_display, create_simple_formula


def generate_info_content_file():
    """Generate complete info_content.py file from metadata."""

    # Load metadata
    metadata = load_metadata()

    # Generate all content
    all_content = generate_all_info_content()

    # Start building the file
    output_lines = [
        '"""',
        'Info Content Repository',
        'AUTO-GENERATED from component_metadata.json',
        'DO NOT EDIT MANUALLY - use scripts/generate_info_content.py to regenerate',
        '"""',
        '',
        'from dash import html',
        'from utils.formula_formatter import create_formula_display, create_simple_formula',
        '',
        '',
        'INFO_CONTENT = {'
    ]

    # Add each component
    for component_id, content in all_content.items():
        # Get the original metadata for formula details
        meta = None
        for page_id, page_data in metadata.items():
            if page_id.startswith('_'):
                continue
            if component_id in page_data:
                meta = page_data[component_id]
                break

        if not meta:
            continue

        # Format the entry
        output_lines.append(f'    "{component_id}": {{')
        output_lines.append(f'        "tooltip": """{content["tooltip"]}""",')
        output_lines.append(f'        "title": """{content["title"]}""",')

        # Create formatted formula
        calc_summary = meta.get('calculation_summary', '')
        formula_desc = meta.get('formula_description', '')

        output_lines.append(f'        "formula": create_simple_formula(')
        output_lines.append(f'            "{content["title"]}",')
        output_lines.append(f'            "{calc_summary}",')
        output_lines.append(f'            "{formula_desc}"')
        output_lines.append(f'        ),')

        # Add Python code
        python_code_escaped = content['python_code'].replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
        output_lines.append(f'        "python_code": """{python_code_escaped}""",')

        # Add SQL code
        sql_code_escaped = content['sql_code'].replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
        output_lines.append(f'        "sql_code": """{sql_code_escaped}"""')

        output_lines.append('    },')
        output_lines.append('')

    output_lines.append('}')

    # Write to file
    output_path = Path(__file__).parent.parent / 'src' / 'config' / 'info_content_generated.py'
    output_path.write_text('\n'.join(output_lines))

    print(f"✓ Generated {len(all_content)} component entries")
    print(f"✓ Written to: {output_path}")
    print(f"\nTo use the generated file:")
    print(f"  1. Review the generated content in info_content_generated.py")
    print(f"  2. If satisfied, rename/replace info_content.py")
    print(f"  3. Or import from info_content_generated instead")


if __name__ == '__main__':
    print("Generating info_content.py from metadata...")
    print("=" * 60)
    generate_info_content_file()
    print("=" * 60)
    print("✓ Complete!")
