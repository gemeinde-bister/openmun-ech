#!/usr/bin/env python3
"""Data Minimization for eCH-0020.

Applies privacy-first filtering to eCH-0020 base delivery:
- Removes VN (AHV number)
- Removes job_data, health_insurance_data
- Removes guardian relationships (keeps parental - father/mother names)
- Removes armed forces, civil defense, fire service data
- Keeps contact_data (c/o addresses for care homes)
- Keeps parent names (nameOfFather/nameOfMother in birthAddonData)
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

from openmun_ech.ech0020.v3 import ECH0020Delivery

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
        description='Data minimization for eCH-0020 base delivery',
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
    print("Loading and filtering eCH-0020 data...")
    delivery = ECH0020Delivery.from_xml(root)

    # Apply eCH-0020 specific filtering
    # delivery.event is a list of events, each with base_delivery_person
    for event in delivery.event:
        if hasattr(event, 'base_delivery_person') and event.base_delivery_person:
            person = event.base_delivery_person

            # Remove VN (always remove - privacy-sensitive)
            if person.person_identification and person.person_identification.vn:
                person.person_identification.vn = None

            # Remove optional privacy-sensitive data
            # NOTE: contact_data is KEPT (contains c/o addresses for care homes)
            person.job_data = None
            person.health_insurance_data = None
            person.armed_forces_data = None
            person.civil_defense_data = None
            person.fire_service_data = None
            person.person_additional_data = None
            person.matrimonial_inheritance_arrangement_data = None
            person.political_right_data = None

            # Remove guardian relationships only (keep parental - father/mother names)
            # NOTE: parental_relationship is KEPT (contains father/mother names for genealogy)
            person.guardian_relationship = []

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

    # Use general diff tool to compare (baseDeliveryPerson in eCH-0020 namespace)
    compare_xml_files(
        original_path=str(input_file),
        filtered_path=str(output_file),
        entity_xpath='.//{http://www.ech.ch/xmlns/eCH-0020/3}baseDeliveryPerson',
        entity_name_xpath='.//{http://www.ech.ch/xmlns/eCH-0044/4}officialName'
    )


if __name__ == '__main__':
    main()
