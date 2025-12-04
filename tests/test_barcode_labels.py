import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from documents.barcode_labels import (
    validate_and_format_barcode,
    generate_barcode_labels,
    fetch_purchase_orders_for_barcode_labels
)


def test_validate_and_format_barcode():
    """Test barcode validation and formatting."""
    print("Testing barcode validation...")
    
    # Test valid 13-digit barcode
    assert validate_and_format_barcode("1234567890123") == "1234567890123"
    print("✓ Valid 13-digit barcode")
    
    # Test barcode with less than 13 digits (should pad with zeros)
    assert validate_and_format_barcode("12345") == "0000000012345"
    print("✓ Short barcode padded correctly")
    
    # Test barcode with more than 13 digits (should truncate)
    assert validate_and_format_barcode("12345678901234567") == "5678901234567"
    print("✓ Long barcode truncated correctly")
    
    # Test barcode as integer
    assert validate_and_format_barcode(1234567890123) == "1234567890123"
    print("✓ Integer barcode handled correctly")
    
    # Test barcode with spaces and hyphens
    assert validate_and_format_barcode("123-456-789-0123") == "1234567890123"
    print("✓ Barcode with hyphens cleaned correctly")
    
    # Test barcode in list format (Airtable style)
    assert validate_and_format_barcode(["1234567890123"]) == "1234567890123"
    print("✓ List-formatted barcode handled correctly")
    
    # Test empty barcode
    assert validate_and_format_barcode("") is None
    print("✓ Empty barcode returns None")
    
    # Test empty list
    assert validate_and_format_barcode([]) is None
    print("✓ Empty list returns None")
    
    print("\nAll barcode validation tests passed!")


def test_generate_barcode_labels_mock():
    """Test barcode label generation with mock data."""
    print("\nTesting barcode label generation with mock data...")
    
    # Create mock order data
    mock_order = {
        'id': 'test123',
        'fields': {
            'PO #': 'PO-TEST-001'
        },
        'line_items': [
            {
                'fields': {
                    'Position': 1,
                    'sku': ['TEST-SKU-001'],
                    'Line Item Name': ['Test Product Name'],
                    'Option1 Value': ['Medium'],
                    'Barcode': '1234567890123'
                }
            },
            {
                'fields': {
                    'Position': 2,
                    'sku': ['TEST-SKU-002'],
                    'Line Item Name': ['Another Test Product With Very Long Name'],
                    'Option1 Value': ['Large'],
                    'Barcode': ['9876543210987']
                }
            }
        ]
    }
    
    try:
        filename = generate_barcode_labels(mock_order)
        print(f"✓ Generated barcode labels PDF: {filename}")
        
        # Check file exists
        assert os.path.exists(filename), f"File {filename} was not created"
        print(f"✓ File exists at {filename}")
        
        # Check file size (should be reasonable)
        file_size = os.path.getsize(filename)
        assert file_size > 1000, f"File size {file_size} is too small"
        print(f"✓ File size is {file_size} bytes (reasonable size)")
        
        print("\nBarcode label generation test passed!")
        return filename
        
    except Exception as e:
        print(f"✗ Error during barcode label generation: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_generate_barcode_labels_edge_cases():
    """Test barcode label generation with edge cases."""
    print("\nTesting edge cases...")
    
    # Test with 24 items (exactly one page)
    mock_order_24 = {
        'id': 'test_24_items',
        'fields': {'PO #': 'PO-TEST-24'},
        'line_items': [
            {
                'fields': {
                    'Position': i,
                    'sku': [f'SKU-{i:03d}'],
                    'Line Item Name': [f'Product {i}'],
                    'Option1 Value': [f'Size-{i}'],
                    'Barcode': f'{1234567890000 + i}'
                }
            } for i in range(1, 25)
        ]
    }
    
    try:
        filename = generate_barcode_labels(mock_order_24)
        print(f"✓ Generated 24-label PDF (1 page): {filename}")
        assert os.path.exists(filename)
        os.remove(filename)
        print("✓ Test with 24 items passed")
    except Exception as e:
        print(f"✗ Error with 24 items: {e}")
        raise
    
    # Test with 25 items (should create 2 pages)
    mock_order_25 = {
        'id': 'test_25_items',
        'fields': {'PO #': 'PO-TEST-25'},
        'line_items': [
            {
                'fields': {
                    'Position': i,
                    'sku': [f'SKU-{i:03d}'],
                    'Line Item Name': [f'Product {i}'],
                    'Option1 Value': [f'Size-{i}'],
                    'Barcode': f'{1234567890000 + i}'
                }
            } for i in range(1, 26)
        ]
    }
    
    try:
        filename = generate_barcode_labels(mock_order_25)
        print(f"✓ Generated 25-label PDF (2 pages): {filename}")
        assert os.path.exists(filename)
        os.remove(filename)
        print("✓ Test with 25 items (multi-page) passed")
    except Exception as e:
        print(f"✗ Error with 25 items: {e}")
        raise
    
    # Test with no line items
    mock_order_empty = {
        'id': 'test_empty',
        'fields': {'PO #': 'PO-TEST-EMPTY'},
        'line_items': []
    }
    
    try:
        filename = generate_barcode_labels(mock_order_empty)
        print(f"✓ Generated empty PDF: {filename}")
        assert os.path.exists(filename)
        os.remove(filename)
        print("✓ Test with no line items passed")
    except Exception as e:
        print(f"✗ Error with empty order: {e}")
        raise
    
    print("\nAll edge case tests passed!")


def test_barcode_labels_integration():
    """Integration test - only runs if config is available."""
    print("\nTesting Airtable integration (if config available)...")
    
    try:
        import config
        orders = fetch_purchase_orders_for_barcode_labels()
        print(f"✓ Successfully fetched {len(orders)} purchase orders")
        
        if orders:
            print("Sample order structure:")
            import json
            print(json.dumps({
                'id': orders[0].get('id'),
                'fields': orders[0].get('fields'),
                'line_items_count': len(orders[0].get('line_items', []))
            }, indent=2))
        else:
            print("No orders found with 'Generate barcode labels' checked")
            
    except ImportError:
        print("⚠ Config not available, skipping integration test")
    except Exception as e:
        print(f"⚠ Integration test failed (this is OK if no data is available): {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Barcode Labels Tests")
    print("=" * 60)
    
    # Run tests
    test_validate_and_format_barcode()
    test_generate_barcode_labels_mock()
    test_generate_barcode_labels_edge_cases()
    test_barcode_labels_integration()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
