import os

def test_file_creation():
    test_file = '/data/dates-wednesdays.txt'
    try:
        with open(test_file, 'w') as f:
            f.write("Test data")
        print(f"File created successfully at {test_file}")
    except Exception as e:
        print(f"Failed to create file: {e}")

test_file_creation()
