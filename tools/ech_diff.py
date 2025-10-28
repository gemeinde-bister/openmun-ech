#!/usr/bin/env python3
"""
General XML Diff Tool for Data Minimization
============================================

Compares original vs filtered XML files and displays a colored diff showing:
- GREEN ✓ = Elements kept in filtered output
- RED ✗ = Elements removed for privacy

This is a reusable utility that works with any XML structure.
"""

import xml.etree.ElementTree as ET
from typing import Optional

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
BOLD = '\033[1m'
RESET = '\033[0m'
DIM = '\033[2m'


def print_element_colored(elem: ET.Element, indent: int, color: str, prefix: str):
    """Print an element with color and indentation, recursively showing all children."""
    ind = '  ' * indent
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

    if len(elem) == 0:  # Leaf element
        if elem.text and elem.text.strip():
            print(f"{color}{prefix}{ind}<{tag}>{elem.text}</{tag}>{RESET}")
        else:
            print(f"{color}{prefix}{ind}<{tag}/>{RESET}")
    else:  # Container element - print with children
        print(f"{color}{prefix}{ind}<{tag}>{RESET}")
        for child in elem:
            print_element_colored(child, indent + 1, color, prefix)
        print(f"{color}{prefix}{ind}</{tag}>{RESET}")


def compare_elements_recursive(orig: ET.Element, filt: ET.Element, indent: int = 0):
    """
    Recursively compare two XML elements and print colored diff.

    Args:
        orig: Original XML element
        filt: Filtered XML element
        indent: Current indentation level
    """
    ind = '  ' * indent

    # Build maps of children by tag
    orig_children = {child.tag: child for child in orig}
    filt_children = {child.tag: child for child in filt}

    # Get all unique child tags (sorted for consistent output)
    all_tags = sorted(set(orig_children.keys()) | set(filt_children.keys()))

    for child_tag in all_tags:
        if child_tag in orig_children and child_tag in filt_children:
            # Element exists in both - need to recurse
            orig_child = orig_children[child_tag]
            filt_child = filt_children[child_tag]

            child_tag_name = child_tag.split('}')[-1] if '}' in child_tag else child_tag

            # Check if leaf element
            if len(orig_child) == 0:
                # Leaf element - just print it green
                if orig_child.text and orig_child.text.strip():
                    print(f"{GREEN}✓ {ind}<{child_tag_name}>{orig_child.text}</{child_tag_name}>{RESET}")
                else:
                    print(f"{GREEN}✓ {ind}<{child_tag_name}/>{RESET}")
            else:
                # Container element - print opening tag and recurse
                print(f"{GREEN}✓ {ind}<{child_tag_name}>{RESET}")
                compare_elements_recursive(orig_child, filt_child, indent + 1)
                print(f"{GREEN}✓ {ind}</{child_tag_name}>{RESET}")

        elif child_tag in orig_children and child_tag not in filt_children:
            # Element only in original - removed (red)
            print_element_colored(orig_children[child_tag], indent, RED, '✗ ')


def compare_xml_files(original_path: str, filtered_path: str,
                     entity_xpath: str, entity_name_xpath: Optional[str] = None,
                     max_entities: Optional[int] = None):
    """
    Compare original and filtered XML files, showing differences for each entity.

    Args:
        original_path: Path to original XML file
        filtered_path: Path to filtered XML file
        entity_xpath: XPath to find entities (e.g., './/person' or './/event')
        entity_name_xpath: Optional XPath within entity to get display name
        max_entities: Maximum number of entities to display (None = all)
    """
    print(f"\n{BOLD}DATA MINIMIZATION - COMPLETE XML DIFF{RESET}")
    print("=" * 80)
    print(f"\nOriginal: {original_path}")
    print(f"Filtered: {filtered_path}")
    print(f"\n{GREEN}✓ GREEN{RESET} = Element KEPT (preserved in output)")
    print(f"{RED}✗ RED{RESET} = Element REMOVED (filtered for privacy)")
    print("\nShowing complete XML structure with all values...\n")

    # Parse both files
    orig_tree = ET.parse(original_path)
    filt_tree = ET.parse(filtered_path)

    # Find all entities
    orig_entities = orig_tree.findall(entity_xpath)
    filt_entities = filt_tree.findall(entity_xpath)

    total_entities = len(orig_entities)

    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}DETAILED PER-ENTITY COMPARISON{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")

    # Compare each entity
    for i, (orig_entity, filt_entity) in enumerate(zip(orig_entities, filt_entities), 1):
        if max_entities is not None and i > max_entities:
            break

        print(f"\n{BOLD}{'=' * 80}{RESET}")

        # Get entity name if xpath provided
        if entity_name_xpath:
            name_elem = orig_entity.find(entity_name_xpath)
            entity_name = name_elem.text if name_elem is not None else "Unknown"
            print(f"{BOLD}ENTITY #{i}: {entity_name}{RESET}")
        else:
            print(f"{BOLD}ENTITY #{i}{RESET}")

        print(f"{BOLD}{'=' * 80}{RESET}\n")

        # Recursively compare all elements
        compare_elements_recursive(orig_entity, filt_entity, indent=0)
        print()

    # Summary
    if max_entities is not None and total_entities > max_entities:
        print(f"{DIM}... and {total_entities - max_entities} more entities (showing first {max_entities} for readability){RESET}")
        print(f"{DIM}Use --max-entities to see more{RESET}\n")

    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}SUMMARY{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")
    print(f"Total entities: {total_entities}")
    print(f"Output file: {filtered_path}")
    print("\nYou can now manually verify each field that was kept vs removed.")


def detect_entity_xpath(xml_path: str) -> tuple:
    """Auto-detect entity xpath based on XML content."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Check for eCH-0020 baseDeliveryPerson
    if root.findall('.//{http://www.ech.ch/xmlns/eCH-0020/3}baseDeliveryPerson'):
        return (
            './/{http://www.ech.ch/xmlns/eCH-0020/3}baseDeliveryPerson',
            './/{http://www.ech.ch/xmlns/eCH-0044/4}officialName'
        )

    # Check for eCH-0011 person (eCH-0099)
    if root.findall('.//{http://www.ech.ch/xmlns/eCH-0011/8}person'):
        return (
            './/{http://www.ech.ch/xmlns/eCH-0011/8}person',
            './/{http://www.ech.ch/xmlns/eCH-0044/4}officialName'
        )

    # Default fallback
    return (
        './/{http://www.ech.ch/xmlns/eCH-0011/8}person',
        './/{http://www.ech.ch/xmlns/eCH-0044/4}officialName'
    )


def main():
    """CLI interface for ech_diff."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Compare two eCH XML files and show colored diff (auto-detects eCH-0020/0099)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('original', help='Original XML file')
    parser.add_argument('filtered', help='Filtered XML file')
    parser.add_argument('--entity-xpath', default=None,
                       help='XPath to find entities (default: auto-detect)')
    parser.add_argument('--name-xpath', default=None,
                       help='XPath to get entity name (default: auto-detect)')
    parser.add_argument('--max-entities', type=int, default=None,
                       help='Maximum entities to show (default: all)')

    args = parser.parse_args()

    # Auto-detect if not specified
    if args.entity_xpath is None or args.name_xpath is None:
        entity_xpath, name_xpath = detect_entity_xpath(args.original)
        if args.entity_xpath is None:
            args.entity_xpath = entity_xpath
        if args.name_xpath is None:
            args.name_xpath = name_xpath

    compare_xml_files(
        original_path=args.original,
        filtered_path=args.filtered,
        entity_xpath=args.entity_xpath,
        entity_name_xpath=args.name_xpath,
        max_entities=args.max_entities
    )


if __name__ == '__main__':
    main()
