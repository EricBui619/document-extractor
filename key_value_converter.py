"""
Key-Value Pair Converter Module
Detects and converts multi-record dictionary-like text blocks into HTML tables
Focuses on converting data that has consistent headers across multiple records
"""

import re
from typing import List, Dict, Tuple, Optional


class KeyValueConverter:
    """Converts multi-record dictionary text blocks into structured tables"""

    # Common separators for key-value pairs
    KV_SEPARATORS = [':', '=', '-', '–', '—']

    # Minimum number of records to consider it a multi-record dictionary
    MIN_RECORDS = 2

    def __init__(self):
        """Initialize KeyValue converter"""
        pass

    def detect_multi_record_dictionary(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect if text contains multiple records with the same structure (same headers)

        Example:
            Name: John Smith
            Age: 35
            Email: john@example.com

            Name: Jane Doe
            Age: 28
            Email: jane@example.com

        Args:
            text: Text content to analyze

        Returns:
            Tuple of (is_multi_record, list_of_headers)
        """
        if not text or len(text.strip()) < 20:
            return (False, [])

        # Split into potential records (separated by blank lines)
        records = self._split_into_records(text)

        if len(records) < self.MIN_RECORDS:
            return (False, [])

        # Extract headers from each record
        all_headers = []
        for record in records:
            headers = self._extract_headers_from_record(record)
            if not headers or len(headers) < 2:  # Need at least 2 fields
                return (False, [])
            all_headers.append(headers)

        # Check if all records have the same headers (in same order)
        if not self._have_consistent_headers(all_headers):
            return (False, [])

        # Return the common headers
        return (True, all_headers[0])

    def _split_into_records(self, text: str) -> List[str]:
        """
        Split text into records based on blank lines or repeated header patterns

        Args:
            text: Text content

        Returns:
            List of record strings
        """
        # First try: split by blank lines
        records = []
        current_record = []

        lines = text.strip().split('\n')

        for line in lines:
            if line.strip() == '':
                # Blank line - end of record
                if current_record:
                    records.append('\n'.join(current_record))
                    current_record = []
            else:
                current_record.append(line)

        # Add last record
        if current_record:
            records.append('\n'.join(current_record))

        # If we only got 1 record, try detecting repeated header patterns
        if len(records) < 2:
            records = self._split_by_repeated_headers(text)

        return records

    def _split_by_repeated_headers(self, text: str) -> List[str]:
        """
        Detect repeated header patterns to split records

        Example:
            Name: John    <- header pattern starts
            Age: 35
            Name: Jane    <- same header repeats, new record starts
            Age: 28
        """
        lines = text.strip().split('\n')
        if len(lines) < 4:
            return []

        # Find first key
        first_key = None
        for line in lines:
            key = self._extract_key_from_line(line)
            if key:
                first_key = key
                break

        if not first_key:
            return []

        # Split whenever we see the first key again
        records = []
        current_record = []

        for line in lines:
            key = self._extract_key_from_line(line)

            if key == first_key and current_record:
                # New record starts
                records.append('\n'.join(current_record))
                current_record = [line]
            else:
                current_record.append(line)

        # Add last record
        if current_record:
            records.append('\n'.join(current_record))

        return records if len(records) >= 2 else []

    def _extract_key_from_line(self, line: str) -> Optional[str]:
        """Extract key from a key-value line"""
        line = line.strip()
        for sep in self.KV_SEPARATORS:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    if key and len(key) < 50:
                        return key
        return None

    def _extract_headers_from_record(self, record: str) -> List[str]:
        """
        Extract headers (keys) from a single record

        Args:
            record: Single record text

        Returns:
            List of header names (keys) in order
        """
        headers = []
        lines = record.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract key from line
            key = self._extract_key_from_line(line)
            if key:
                headers.append(key)

        return headers

    def _have_consistent_headers(self, all_headers: List[List[str]]) -> bool:
        """
        Check if all records have the same headers in the same order

        Args:
            all_headers: List of header lists from each record

        Returns:
            True if all headers match
        """
        if not all_headers:
            return False

        first_headers = all_headers[0]

        for headers in all_headers[1:]:
            if headers != first_headers:
                return False

        return True

    def parse_multi_record_dictionary(self, text: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Parse text into structured records

        Args:
            text: Text content with multiple records

        Returns:
            Tuple of (headers, list_of_record_dicts)
        """
        is_multi_record, headers = self.detect_multi_record_dictionary(text)

        if not is_multi_record:
            return ([], [])

        records = self._split_into_records(text)
        parsed_records = []

        for record in records:
            record_dict = {}
            lines = record.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Parse key-value
                for sep in self.KV_SEPARATORS:
                    if sep in line:
                        parts = line.split(sep, 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key and value:
                                record_dict[key] = value
                                break

            if record_dict:
                parsed_records.append(record_dict)

        return (headers, parsed_records)

    def convert_to_html_table(self, text: str, caption: str = None) -> str:
        """
        Convert multi-record dictionary text into HTML table

        Args:
            text: Text content with multiple records
            caption: Optional table caption

        Returns:
            HTML table string or None if not convertible
        """
        headers, records = self.parse_multi_record_dictionary(text)

        if not headers or len(records) < self.MIN_RECORDS:
            return None

        html_parts = ['<table style="border-collapse: collapse; width: 100%;">']

        # Add caption if provided
        if caption:
            html_parts.append(f'  <caption>{self._escape_html(caption)}</caption>')

        # Add header row
        html_parts.append('  <thead>')
        html_parts.append('    <tr>')
        for header in headers:
            header_escaped = self._escape_html(header)
            html_parts.append(f'      <th style="text-align: left; padding: 8px; background-color: #4CAF50; color: white; border: 1px solid #ddd; font-weight: bold;">{header_escaped}</th>')
        html_parts.append('    </tr>')
        html_parts.append('  </thead>')

        # Add data rows
        html_parts.append('  <tbody>')
        for i, record in enumerate(records):
            # Alternate row colors for better readability
            bg_color = '#f9f9f9' if i % 2 == 0 else '#ffffff'
            html_parts.append('    <tr>')
            for header in headers:
                value = record.get(header, '')
                value_escaped = self._escape_html(value)
                html_parts.append(f'      <td style="text-align: left; padding: 8px; border: 1px solid #ddd; background-color: {bg_color};">{value_escaped}</td>')
            html_parts.append('    </tr>')
        html_parts.append('  </tbody>')

        html_parts.append('</table>')

        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return text

        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }

        for char, escape in replacements.items():
            text = text.replace(char, escape)

        return text

    def convert_content_item(self, content_item: Dict) -> Dict:
        """
        Convert a content item from text to table if it contains multi-record dictionary

        Args:
            content_item: Content item dictionary from extraction

        Returns:
            Modified content item (converted to table if applicable)
        """
        # Only process text content (paragraphs)
        if content_item.get('type') not in ['paragraph', 'text']:
            return content_item

        text = content_item.get('content', '')

        # Check if it's a multi-record dictionary
        is_multi_record, headers = self.detect_multi_record_dictionary(text)
        if not is_multi_record:
            return content_item

        # Convert to table
        table_html = self.convert_to_html_table(text)

        if not table_html:
            return content_item

        # Create new table content item
        table_item = content_item.copy()
        table_item['type'] = 'table'
        table_item['html'] = table_html
        table_item['original_content'] = text  # Keep original for reference

        # Update metadata
        if 'metadata' not in table_item:
            table_item['metadata'] = {}

        _, records = self.parse_multi_record_dictionary(text)
        table_item['metadata']['row_count'] = len(records)
        table_item['metadata']['column_count'] = len(headers)
        table_item['metadata']['converted_from_kv'] = True
        table_item['metadata']['headers'] = headers

        return table_item

    def process_extracted_content(self, content: Dict) -> Dict:
        """
        Process all content items and convert multi-record dictionaries to tables

        Args:
            content: Extracted content dictionary

        Returns:
            Modified content with multi-record dictionaries converted to tables
        """
        if 'content_items' not in content:
            return content

        converted_items = []
        conversion_count = 0

        for item in content['content_items']:
            converted_item = self.convert_content_item(item)
            converted_items.append(converted_item)

            # Track conversions
            if converted_item.get('type') == 'table' and \
               converted_item.get('metadata', {}).get('converted_from_kv'):
                conversion_count += 1

        content['content_items'] = converted_items

        # Update legacy format (tables list)
        if conversion_count > 0:
            if 'tables' not in content:
                content['tables'] = []

            # Add converted tables to tables list
            for item in converted_items:
                if item.get('type') == 'table' and \
                   item.get('metadata', {}).get('converted_from_kv'):
                    content['tables'].append(item)

        return content


def main():
    """Test the key-value converter"""

    converter = KeyValueConverter()

    # Test case 1: Multi-record dictionary separated by blank lines
    text1 = """Name: John Smith
Age: 35
Email: john@example.com

Name: Jane Doe
Age: 28
Email: jane@example.com

Name: Bob Johnson
Age: 42
Email: bob@example.com"""

    print("Test 1: Multi-record dictionary (blank line separators)")
    is_multi, headers = converter.detect_multi_record_dictionary(text1)
    print(f"Is multi-record: {is_multi}")
    print(f"Headers: {headers}")

    if is_multi:
        headers, records = converter.parse_multi_record_dictionary(text1)
        print(f"Parsed {len(records)} records")
        for i, record in enumerate(records, 1):
            print(f"  Record {i}: {record}")

        print("\nHTML Table:")
        print(converter.convert_to_html_table(text1))

    print("\n" + "="*80 + "\n")

    # Test case 2: Multi-record without blank lines (repeated header pattern)
    text2 = """Product: Laptop
Price: $999
Stock: 15
Product: Mouse
Price: $25
Stock: 150
Product: Keyboard
Price: $79
Stock: 80"""

    print("Test 2: Multi-record dictionary (repeated header pattern)")
    is_multi, headers = converter.detect_multi_record_dictionary(text2)
    print(f"Is multi-record: {is_multi}")
    print(f"Headers: {headers}")

    if is_multi:
        headers, records = converter.parse_multi_record_dictionary(text2)
        print(f"Parsed {len(records)} records")
        for i, record in enumerate(records, 1):
            print(f"  Record {i}: {record}")

        print("\nHTML Table:")
        print(converter.convert_to_html_table(text2))

    print("\n" + "="*80 + "\n")

    # Test case 3: Single record (should NOT convert)
    text3 = """Name: John Smith
Age: 35
Email: john@example.com
Phone: (555) 123-4567"""

    print("Test 3: Single record (should NOT convert)")
    is_multi, headers = converter.detect_multi_record_dictionary(text3)
    print(f"Is multi-record: {is_multi}")
    print(f"Headers: {headers}")

    print("\n" + "="*80 + "\n")

    # Test case 4: Different headers (should NOT convert)
    text4 = """Name: John Smith
Age: 35

Product: Laptop
Price: $999"""

    print("Test 4: Different headers (should NOT convert)")
    is_multi, headers = converter.detect_multi_record_dictionary(text4)
    print(f"Is multi-record: {is_multi}")
    print(f"Headers: {headers}")

    print("\n" + "="*80 + "\n")

    # Test case 5: Content item conversion
    content_item = {
        'type': 'paragraph',
        'content': text1,
        'position': {'x_start': 10, 'y_start': 20, 'x_end': 90, 'y_end': 40}
    }

    print("Test 5: Content item conversion")
    converted = converter.convert_content_item(content_item)
    print(f"Original type: paragraph")
    print(f"Converted type: {converted['type']}")
    print(f"Has HTML: {'html' in converted}")
    print(f"Metadata: {converted.get('metadata', {})}")


if __name__ == '__main__':
    main()
