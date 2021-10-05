"""Contains support functions for the module pyads_ex.py

:author: David Browne <davidabrowne@gmail.com>
:license: MIT, see license file or https://opensource.org/licenses/MIT
:created on: 2021-10-50

"""
from typing import Any, Tuple, List, Type, Optional, Union
import socket
from contextlib import closing
import struct

from .constants import (
    DATATYPE_MAP,
    ads_type_to_ctype,
    PLCTYPE_STRING,
    PORT_REMOTE_UDP,
    ADST_STRING,
    ADST_WSTRING,
)
from .structs import SAdsSymbolEntry
from .errorcodes import ERROR_CODES


class ADSError(Exception):
    """Error class for errors related to ADS communication."""

    def __init__(
        self, err_code: Optional[int] = None, text: Optional[str] = None
    ) -> None:
        if err_code is not None:
            self.err_code = err_code
            try:
                self.msg = "{} ({}). ".format(ERROR_CODES[self.err_code], self.err_code)
            except KeyError:
                self.msg = "Unknown Error ({0}). ".format(self.err_code)
        else:
            self.msg = ""

        if text is not None:
            self.msg += text

    def __str__(self):
        # type: () -> str
        """Return text representation of the object."""
        return "ADSError: " + self.msg


def send_raw_udp_message(
    ip_address: str, message: bytes, expected_return_length: int
) -> Tuple[bytes, Tuple[str, int]]:
    """Send a raw UDP message to the PLC and return the response.

    :param str ip_address: ip address of the PLC
    :param bytes message: the message to send to the PLC
    :param int expected_return_length: number of bytes to expect in response
    :rtype: Tuple[bytes, Tuple[str, int]]
    :return: A tuple containing the response and a tuple containing the IP address and port of the
             sending socket
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:  # UDP
        # Listen on any available port for the response from the PLC
        sock.bind(("", 0))

        # Send our data to the PLC
        sock.sendto(message, (ip_address, PORT_REMOTE_UDP))

        # Response should come in in less than .5 seconds, but wait longer to account for slow
        # communications
        sock.settimeout(5)

        # Allow TimeoutError to be raised so user can handle it how they please
        return sock.recvfrom(expected_return_length)


def type_is_string(plc_type: Type) -> bool:
    """Return true if the given class is a string type."""

    # If single char
    if plc_type == PLCTYPE_STRING:
        return True

    # If char array
    if type(plc_type).__name__ == "PyCArrayType":
        if plc_type._type_ == PLCTYPE_STRING:
            return True

    return False


def get_value_from_ctype_data(read_data: Optional[Any], plc_type: Type) -> Any:
    """Convert ctypes data object to a regular value based on the PLCTYPE_* property.

    Typical usage is:

    .. code:: python

        obj = my_plc_type.from_buffer(my_buffer)
        value = get_value_from_ctype_data(obj, my_plc_type)

    :param read_data: ctypes._CData object
    :param plc_type: pyads.PLCTYPE_* constant (i.e. a ctypes-like type)
    """

    if read_data is None:
        return None

    if type_is_string(plc_type):
        return read_data.value.decode("utf-8")

    if type(plc_type).__name__ == "PyCArrayType":
        return [i for i in read_data]

    if hasattr(read_data, "value"):
        return read_data.value

    return read_data  # Just return the object itself, don't throw an error
