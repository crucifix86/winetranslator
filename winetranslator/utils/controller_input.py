"""
Controller input detection for button remapping.

Detects button presses and joystick axes from /dev/input/js* devices.
"""

import struct
import time
import os
import glob
from typing import Optional, Tuple, Callable
from pathlib import Path


class ControllerInput:
    """Handles controller input detection for button remapping."""

    # Event types from Linux joystick API
    JS_EVENT_BUTTON = 0x01
    JS_EVENT_AXIS = 0x02
    JS_EVENT_INIT = 0x80

    def __init__(self, device_path: Optional[str] = None):
        """
        Initialize controller input detector.

        Args:
            device_path: Path to joystick device (e.g., /dev/input/js0).
                        If None, auto-detects first available controller.
        """
        if device_path is None:
            device_path = self._find_controller()

        if device_path is None:
            raise RuntimeError("No controller found")

        self.device_path = device_path
        self.device_fd = None
        self.device_name = self._get_device_name()
        self.guid = self._get_device_guid()

    def _find_controller(self) -> Optional[str]:
        """Find the first available joystick device."""
        devices = glob.glob('/dev/input/js*')
        if devices:
            return sorted(devices)[0]  # Return js0, js1, etc. in order
        return None

    def _get_device_name(self) -> str:
        """Get the device name from sysfs."""
        try:
            # Extract device number from /dev/input/jsN
            device_num = self.device_path.split('js')[-1]
            name_path = f'/sys/class/input/js{device_num}/device/name'

            if os.path.exists(name_path):
                with open(name_path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass

        return "Unknown Controller"

    def _get_device_guid(self) -> str:
        """
        Get SDL-compatible GUID for the controller.

        Format: bustype-vendor-product-version (in hex)
        For now, we'll generate a simple GUID based on the device name.
        """
        # Try to read device info from sysfs
        try:
            device_num = self.device_path.split('js')[-1]

            # Try to get vendor/product IDs
            event_devices = glob.glob(f'/sys/class/input/js{device_num}/device/event*/device/id/*')

            vendor = "0000"
            product = "0000"

            for path in event_devices:
                if 'vendor' in path:
                    with open(path, 'r') as f:
                        vendor = f.read().strip().replace('0x', '')
                elif 'product' in path:
                    with open(path, 'r') as f:
                        product = f.read().strip().replace('0x', '')

            # Generate SDL2-compatible GUID
            # Format: 03000000VVVV0000PPPP000000000000
            # Where V = vendor ID, P = product ID
            guid = f"03000000{vendor:0>4}0000{product:0>4}000000000000"
            return guid
        except Exception:
            pass

        # Fallback: Generate GUID from device name hash
        import hashlib
        hash_value = hashlib.md5(self.device_name.encode()).hexdigest()
        return hash_value[:32]

    def open(self):
        """Open the joystick device for reading."""
        if self.device_fd is None:
            self.device_fd = open(self.device_path, 'rb')

    def close(self):
        """Close the joystick device."""
        if self.device_fd:
            self.device_fd.close()
            self.device_fd = None

    def wait_for_input(self, timeout: float = 30.0) -> Optional[Tuple[str, int]]:
        """
        Wait for a button press or axis movement.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            Tuple of (input_type, input_number) where input_type is 'button' or 'axis',
            or None if timeout occurs.

        Example:
            ('button', 0) for button 0
            ('axis', 2) for axis 2
        """
        if self.device_fd is None:
            self.open()

        start_time = time.time()

        # Track initial axis values to detect movement
        initial_axes = {}
        axis_threshold = 16000  # Threshold for axis movement (out of 32767)

        while time.time() - start_time < timeout:
            # Read joystick event (8 bytes)
            try:
                event = self.device_fd.read(8)
                if len(event) < 8:
                    break

                # Parse event structure
                # struct js_event {
                #     __u32 time;     /* event timestamp in milliseconds */
                #     __s16 value;    /* value */
                #     __u8 type;      /* event type */
                #     __u8 number;    /* axis/button number */
                # };
                timestamp, value, event_type, number = struct.unpack('IhBB', event)

                # Ignore init events
                if event_type & self.JS_EVENT_INIT:
                    if event_type & self.JS_EVENT_AXIS:
                        # Store initial axis position
                        initial_axes[number] = value
                    continue

                # Button press (value = 1 means pressed, 0 means released)
                if event_type == self.JS_EVENT_BUTTON and value == 1:
                    return ('button', number)

                # Axis movement (detect significant movement from initial position)
                if event_type == self.JS_EVENT_AXIS:
                    if number in initial_axes:
                        initial_value = initial_axes[number]
                    else:
                        initial_value = 0
                        initial_axes[number] = value

                    # Check if axis moved significantly
                    if abs(value - initial_value) > axis_threshold:
                        # Determine axis direction
                        axis_str = f"a{number}"
                        if value < initial_value:
                            axis_str += "-"  # Negative direction
                        else:
                            axis_str += "+"  # Positive direction
                        return ('axis', axis_str)

            except Exception as e:
                print(f"Error reading controller input: {e}")
                break

            # Small delay to prevent CPU spinning
            time.sleep(0.01)

        return None

    def get_default_mapping(self) -> str:
        """
        Get the default SDL controller mapping string.

        Returns:
            SDL mapping string in format: "GUID,name,a:b0,b:b1,..."
        """
        # Standard Xbox controller layout (most common default)
        mapping = (
            f"{self.guid},{self.device_name},"
            "a:b0,b:b1,x:b2,y:b3,"  # Face buttons
            "back:b6,start:b7,guide:b8,"  # Special buttons
            "leftshoulder:b4,rightshoulder:b5,"  # Bumpers
            "leftstick:b9,rightstick:b10,"  # Stick clicks
            "leftx:a0,lefty:a1,rightx:a2,righty:a3,"  # Stick axes
            "lefttrigger:a4,righttrigger:a5,"  # Triggers
            "dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2"  # D-pad
        )
        return mapping

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
