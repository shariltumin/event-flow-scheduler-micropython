import sys
sys.path.insert(0, '.')

from ringbuffer import Ring

def test_ring_creation():
    print("Testing Ring creation...")
    ring = Ring(1024)
    assert ring.size == 1024
    assert ring.count == 0
    assert ring.is_empty() == True
    print("✓ Ring creation passed")

def test_invalid_size():
    print("Testing invalid size...")
    try:
        ring = Ring(4)
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    print("✓ invalid size handling passed")

def test_put_get():
    print("Testing put() and get()...")
    ring = Ring(256)
    
    ring.put(1, b"Hello")
    ring.put(2, b"World")
    
    msg_id, msg = ring.get()
    assert msg_id == 1
    assert msg == b"Hello"
    
    msg_id, msg = ring.get()
    assert msg_id == 2
    assert msg == b"World"
    
    print("✓ put() and get() passed")

def test_peek():
    print("Testing peek()...")
    ring = Ring(256)
    
    ring.put(1, b"Test")
    
    result = ring.peek()
    assert result is not None
    msg_id, msg = result
    assert msg_id == 1
    assert msg == b"Test"
    
    result = ring.peek()
    assert result is not None
    msg_id, msg = result
    assert msg_id == 1
    
    print("✓ peek() passed")

def test_pull():
    print("Testing pull()...")
    ring = Ring(256)
    
    ring.put(1, b"First")
    ring.put(2, b"Second")
    ring.put(3, b"Third")
    
    msg_id, msg = ring.pull(2)
    assert msg_id == 2
    assert msg == b"Second"
    
    ids = ring.list()
    assert 2 not in ids
    assert 1 in ids
    assert 3 in ids
    
    print("✓ pull() passed")

def test_list():
    print("Testing list()...")
    ring = Ring(256)
    
    ring.put(1, b"A")
    ring.put(2, b"B")
    ring.put(3, b"C")
    
    ids = ring.list()
    assert ids == [1, 2, 3]
    
    ring.get()
    ids = ring.list()
    assert ids == [2, 3]
    
    print("✓ list() passed")

def test_is_empty():
    print("Testing is_empty()...")
    ring = Ring(256)
    
    assert ring.is_empty() == True
    ring.put(1, b"Test")
    assert ring.is_empty() == False
    ring.get()
    assert ring.is_empty() == True
    
    print("✓ is_empty() passed")

def test_is_full():
    print("Testing is_full()...")
    ring = Ring(20)
    
    assert ring.is_full() == False
    ring.put(1, b"1234567890")
    assert ring.is_full() == False
    
    try:
        ring.put(2, b"1234567890")
        assert False, "Should raise MemoryError"
    except MemoryError:
        pass
    
    print("✓ is_full() passed")

def test_clear():
    print("Testing clear()...")
    ring = Ring(256)
    
    ring.put(1, b"Test1")
    ring.put(2, b"Test2")
    
    ring.clear()
    assert ring.is_empty() == True
    assert ring.count == 0
    assert ring.head == 0
    assert ring.tail == 0
    
    print("✓ clear() passed")

def test_wraparound():
    print("Testing wraparound...")
    ring = Ring(32)
    
    ring.put(1, b"12345")
    ring.put(2, b"67890")
    
    ring.get()
    
    ring.put(3, b"ABCDE")
    
    msg_id, msg = ring.get()
    assert msg_id == 2
    assert msg == b"67890"
    
    msg_id, msg = ring.get()
    assert msg_id == 3
    assert msg == b"ABCDE"
    
    print("✓ wraparound passed")

def test_invalid_msg_id():
    print("Testing invalid msg_id...")
    ring = Ring(256)
    
    try:
        ring.put(0, b"Test")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    try:
        ring.put(65536, b"Test")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ invalid msg_id handling passed")

def test_invalid_msg_bytes():
    print("Testing invalid msg_bytes...")
    ring = Ring(256)
    
    try:
        ring.put(1, "Not bytes")
        assert False, "Should raise TypeError"
    except TypeError:
        pass
    
    print("✓ invalid msg_bytes handling passed")

def test_message_too_large():
    print("Testing message too large...")
    ring = Ring(256)
    
    try:
        ring.put(1, b"X" * 300)
        assert False, "Should raise MemoryError"
    except MemoryError:
        pass
    
    print("✓ message too large handling passed")

def test_empty_get():
    print("Testing get() on empty buffer...")
    ring = Ring(256)
    
    msg_id, msg = ring.get()
    assert msg_id == 0
    assert msg == b''
    
    print("✓ empty get() passed")

def test_empty_peek():
    print("Testing peek() on empty buffer...")
    ring = Ring(256)
    
    result = ring.peek()
    assert result is None
    
    print("✓ empty peek() passed")

def test_pull_not_found():
    print("Testing pull() not found...")
    ring = Ring(256)
    
    ring.put(1, b"Test")
    
    msg_id, msg = ring.pull(99)
    assert msg_id == 0
    assert msg == b''
    
    print("✓ pull() not found passed")

def test_len():
    print("Testing __len__()...")
    ring = Ring(256)
    
    assert len(ring) == 0
    ring.put(1, b"Test")
    assert len(ring) > 0
    ring.get()
    assert len(ring) == 0
    
    print("✓ __len__() passed")

def test_repr():
    print("Testing __repr__()...")
    ring = Ring(256)
    
    repr_str = repr(ring)
    assert "Ring" in repr_str
    assert "256" in repr_str
    
    print("✓ __repr__() passed")

def test_multiple_operations():
    print("Testing multiple operations...")
    ring = Ring(512)
    
    for i in range(10):
        ring.put(i+1, f"Message {i}".encode())
    
    ids = ring.list()
    assert len(ids) == 10
    
    for i in range(5):
        ring.get()
    
    ids = ring.list()
    assert len(ids) == 5
    
    msg_id, msg = ring.pull(8)
    assert msg_id == 8
    
    ids = ring.list()
    assert 8 not in ids
    assert len(ids) == 4
    
    print("✓ multiple operations passed")

def run_all_tests():
    print("=" * 50)
    print("Running Ring Buffer Tests")
    print("=" * 50)
    
    tests = [
        test_ring_creation,
        test_invalid_size,
        test_put_get,
        test_peek,
        test_pull,
        test_list,
        test_is_empty,
        test_is_full,
        test_clear,
        test_wraparound,
        test_invalid_msg_id,
        test_invalid_msg_bytes,
        test_message_too_large,
        test_empty_get,
        test_empty_peek,
        test_pull_not_found,
        test_len,
        test_repr,
        test_multiple_operations,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
