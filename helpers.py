from ipaddress import ip_address
import socket
import netifaces

dest_ip = "2.2.103.115"
dest_port = 6454


def find_matching_interface(ip_msb):
    """Find the first interface IP that starts with the given MSB (e.g., 2 or 10)"""
    subnet_prefix = f"{ip_msb}."
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            for addr_info in addrs[netifaces.AF_INET]:
                ip = addr_info['addr']
                if ip.startswith(subnet_prefix):
                    print(
                        f"Found matching interface: {interface} with IP {ip}")
                    return ip, interface
    return None, None


def open_connection():
    source_ip, interface = find_matching_interface(2)

    if source_ip is None:
        print(
            "Warning: No interface found with IP starting with '2.'. Binding to 0.0.0.0"
        )
        print(
            "Note: in many cases this will work fine. Error will be seen if there exists another network interface with a /8 subnet"
        )
        source_ip = "0.0.0.0"
        interface = "all"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.0)  # in secs

    # enable broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # On macOS, explicitly bind socket to the specific interface
    if interface != "all":
        # IP_BOUND_IF socket option for macOS (25 is the value for IP_BOUND_IF)
        IP_BOUND_IF = 25
        if_index = socket.if_nametoindex(interface)
        sock.setsockopt(socket.IPPROTO_IP, IP_BOUND_IF, if_index)
        print(f"Socket bound to interface {interface} (index {if_index})")

    sock.bind((source_ip, 0))

    print(
        f"UDP socket opened and bound to {source_ip}:6454 on interface {interface}"
    )
    return sock


def send(packet, sock):
    sock.sendto(packet, (dest_ip, dest_port))


def wait_for_response(sock):
    try:
        data, address = sock.recvfrom(1024)  # buffer size
        return True, data
    except TimeoutError:
        print("Timed out waiting for response")
        return False, None


def send_packet(packet, sock, expect_response):
    packet_bytes = packet.pack()
    send(packet_bytes, sock)
    if expect_response:
        success, response = wait_for_response(sock)
        if success:
            return response


def prompt_for_number(prompt_text):
    valid_input = False
    while not valid_input:
        num_str = input(prompt_text)
        try:
            num = int(num_str)
            valid_input = True
        except ValueError:
            print("Not a valid number")

    return num


# allowed_values doesn't have to be a continuous range
def prompt_for_number_in_range(prompt_text, allowed_values):
    valid_input = False
    while not valid_input:
        num_str = input(prompt_text)
        try:
            num = int(num_str)
            if num in allowed_values:
                valid_input = True
            else:
                print(f"Number {num} not in allowed values")
        except ValueError:
            print("Not a valid number")

    return num


def prompt_for_string_in_range(prompt_text, allowed_values):
    valid_input = False
    while not valid_input:
        temp_str = input(prompt_text)
        for allowed_str in allowed_values:
            if temp_str == allowed_str:
                valid_input = True

        if not valid_input:
            print(
                f"String {temp_str} not in allowed values ({allowed_values})")

    return temp_str


def prompt_for_ip(prompt_text):
    valid_input = False
    while not valid_input:
        ip_str = input(prompt_text)
        try:
            ip = ip_address(ip_str)
            valid_input = True
        except ValueError:
            print("Not a valid IP")

    return ip


def bswap16(val):
    return ((val & 0xFF) << 8) | ((val & 0xFF00) >> 8)


def bswap32(val):
    return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) | (
        (val & 0xFF0000) >> 8) | ((val & 0xFF000000) >> 24)


def uint32_to_big_endian_bytes(val):
    return [(val & 0xFF000000) >> 24, (val & 0x00FF0000) >> 16,
            (val & 0x0000FF00) >> 8, val & 0x000000FF]
