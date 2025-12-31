#
# MIT License
# 
# Copyright (c) 2025 shariltumin
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

class Ring:
    def __init__(my, size):
        if not isinstance(size, int) or size < 8:
            raise ValueError('size must be an integer >= 8')
        my.size = size
        my.buffer = bytearray(size)
        my.head = 0  # Write pointer
        my.tail = 0  # Read pointer
        my.count = 0 # Number of bytes in buffer

    def _advance(my, pointer, n):
        return (pointer + n) % my.size

    def _space_left(my):
        return my.size - my.count

    def _head_tail(my):
        return my.head, my.tail

    def is_empty(my):
        """Check if the buffer is empty."""
        return my.count == 0

    def is_full(my):
        """Check if the buffer is full."""
        return my.count == my.size

    def put(my, msg_id, msg_bytes):
        if not (1 <= msg_id <= 65535): # msg_id 0 is reserved for deleted messages
           raise ValueError('msg_id must be between 1 and 65535')
        if not isinstance(msg_bytes, (bytes, bytearray)):
            raise TypeError('msg_bytes must be bytes or bytearray')
        msg_len = len(msg_bytes)
        if msg_len > 65535:
            raise ValueError('message length exceeds maximum of 65535 bytes')
        total_len = 4 + msg_len  # 2 bytes ID, 2 bytes size, message

        if my._space_left() < total_len:
            raise MemoryError("Not enough space in buffer")

        # Prepare header
        id_bytes = msg_id.to_bytes(2, 'big')
        size_bytes = msg_len.to_bytes(2, 'big')
        packet = id_bytes + size_bytes + msg_bytes

        # Write packet to buffer, handle wraparound
        for b in packet:
            my.buffer[my.head] = b
            my.head = my._advance(my.head, 1)
        my.count += total_len

    def get_header(my, ptr):
        # Read header
        id_bytes = bytes([
           my.buffer[ptr],
           my.buffer[my._advance(ptr, 1)]
        ])
        size_bytes = bytes([
           my.buffer[my._advance(ptr, 2)],
           my.buffer[my._advance(ptr, 3)]
        ])
        msg_id = int.from_bytes(id_bytes, 'big')
        msg_len = int.from_bytes(size_bytes, 'big')
        return msg_id, 4 + msg_len

    def get(my):
        while my.count >= 4:
            # Read header
            msg_id, total_msg_len = my.get_header(my.tail)

            if my.count < total_msg_len:
                return (0, b'')  # Not enough for full message

            if msg_id != 0:
                # Valid message, consume it
                result = bytearray(total_msg_len)
                for i in range(total_msg_len):
                    result[i] = my.buffer[my.tail]
                    my.tail = my._advance(my.tail, 1)
                my.count -= total_msg_len
                msg = bytes(result[4:])
                return (msg_id, msg)
            else:
                # Deleted message, skip it
                my.tail = my._advance(my.tail, total_msg_len)
                my.count -= total_msg_len
                # Continue loop to check next message

        return (0, b'')

    def peek(my):
        # Skip deleted messages (ID == 0)
        scan_ptr = my.tail
        bytes_scanned = 0

        while bytes_scanned < my.count:
            if my.count - bytes_scanned < 4:
                return None  # Not enough for header

            msg_id, total_msg_len = my.get_header(scan_ptr)

            if my.count - bytes_scanned < total_msg_len:
                return None  # Not enough for full message

            if msg_id != 0:
                # Found a valid message
                result = bytearray(total_msg_len)
                temp_ptr = scan_ptr
                for i in range(total_msg_len):
                    result[i] = my.buffer[temp_ptr]
                    temp_ptr = my._advance(temp_ptr, 1)
                msg = bytes(result[4:])
                return (msg_id, msg)
            else:
                # Skip this deleted message
                scan_ptr = my._advance(scan_ptr, total_msg_len)
                bytes_scanned += total_msg_len

        return None

    def clean_up(my):
        # delete block with id == 0
        while my.count >= 4:
            msg_id, total_msg_len = my.get_header(my.tail)

            if msg_id == 0:
                # Deleted message, skip it
                my.tail = my._advance(my.tail, total_msg_len)
                my.count -= total_msg_len
                # Continue loop to check next message
            else:
                return

    def pull(my, wanted_id):
        # Validate wanted_id
        if not (1 <= wanted_id <= 65535):
            return (0, b'')

        # Scan for the first message with the given ID
        scan_ptr = my.tail
        bytes_scanned = 0

        while bytes_scanned < my.count:
            if my.count - bytes_scanned < 4:
                break  # Not enough for header

            id_pos = scan_ptr
            msg_id, total_msg_len = my.get_header(scan_ptr)

            if my.count - bytes_scanned < total_msg_len:
                break  # Not enough for full message

            if msg_id == wanted_id:
                # Mark as deleted (ID = 0)
                my.buffer[id_pos] = 0
                my.buffer[my._advance(id_pos, 1)] = 0
                # Extract message
                result = bytearray(total_msg_len)
                temp_ptr = scan_ptr
                for i in range(total_msg_len):
                    result[i] = my.buffer[temp_ptr]
                    temp_ptr = my._advance(temp_ptr, 1)
                msg = bytes(result[4:])

                # If this message is at the tail, advance tail and reclaim space
                if scan_ptr == my.tail:
                    my.tail = my._advance(my.tail, total_msg_len)
                    my.count -= total_msg_len
                else:
                    my.clean_up() # delete blocks with id==0

                return (msg_id, msg)

            # Move to next message
            scan_ptr = my._advance(scan_ptr, total_msg_len)
            bytes_scanned += total_msg_len

        return (0, b'')

    def list(my):
        """Return a list of all message IDs in the buffer, in order (excluding deleted ones)."""
        ids = []
        scan_ptr = my.tail
        bytes_scanned = 0

        while bytes_scanned < my.count:
            if my.count - bytes_scanned < 4:
                break  # Not enough for header

            msg_id, total_msg_len = my.get_header(scan_ptr)

            if my.count - bytes_scanned < total_msg_len:
                break  # Not enough for full message

            if msg_id != 0:
                ids.append(msg_id)
            scan_ptr = my._advance(scan_ptr, total_msg_len)
            bytes_scanned += total_msg_len

        return ids

    def clear(my):
        """Clear the buffer, resetting all pointers and count."""
        my.head = 0
        my.tail = 0
        my.count = 0

    def __len__(my):
        """Return the number of bytes currently in the buffer."""
        return my.count

    def __repr__(my):
        """Return a string representation of the Ring buffer."""
        return f"Ring(size={my.size}, count={my.count}, head={my.head}, tail={my.tail})"

