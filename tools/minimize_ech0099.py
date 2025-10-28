#!/usr/bin/env python3
"""Data Minimization for eCH-0099.

Applies privacy-first filtering to eCH-0099 base delivery:
- Removes VN (AHV number)
- Removes contact_data, job_data, health_insurance_data
- Replaces vendor info with openmun (by default)

Then shows complete XML diff with color coding.
"""

import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from openmun_ech.ech0099.v2 import ECH0099Delivery

# Import general diff tool
from ech_diff import compare_xml_files


def get_project_version():
    """Read version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / 'pyproject.toml'
    try:
        with open(pyproject_path, 'r') as f:
            content = f.read()
            match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return '0.1.0'


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Data minimization for eCH-0099 base delivery',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', type=Path, help='Input XML file')
    parser.add_argument('output', type=Path, help='Output XML file')
    parser.add_argument('--keep-original-vendor', action='store_true',
                       help='Keep original vendor information (default: replace with openmun)')

    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    keep_vendor = args.keep_original_vendor

    # Parse original
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Parse to Pydantic and filter
    print("Loading and filtering eCH-0099 data...")
    delivery = ECH0099Delivery.from_xml(root)

    # Apply eCH-0099 specific filtering
    for reported_person in delivery.reported_person:
        person = reported_person.base_data.person

        # Remove VN (always remove - privacy-sensitive)
        if person.person_identification and person.person_identification.vn:
            person.person_identification.vn = None

        # Remove optional privacy-sensitive data
        if hasattr(person, 'contact_data'):
            person.contact_data = None
        if hasattr(person, 'job_data'):
            person.job_data = None
        if hasattr(person, 'health_insurance_data'):
            person.health_insurance_data = None

    # Replace vendor information (unless --keep-original-vendor)
    if not keep_vendor:
        if hasattr(delivery.delivery_header, 'sending_application') and delivery.delivery_header.sending_application:
            app = delivery.delivery_header.sending_application
            app.manufacturer = "openmun"
            app.product = "openmun"
            app.product_version = get_project_version()

    # Export filtered XML
    filtered_root = delivery.to_xml()
    filtered_tree = ET.ElementTree(filtered_root)
    ET.indent(filtered_tree, space='  ')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    filtered_tree.write(output_file, encoding='utf-8', xml_declaration=True)

    print(f"Filtered file saved to: {output_file}\n")

    # Use general diff tool to compare (persons in eCH-0011 namespace)
    compare_xml_files(
        original_path=str(input_file),
        filtered_path=str(output_file),
        entity_xpath='.//{http://www.ech.ch/xmlns/eCH-0011/8}person',
        entity_name_xpath='.//{http://www.ech.ch/xmlns/eCH-0044/4}officialName'
    )


if __name__ == '__main__':
    main()
