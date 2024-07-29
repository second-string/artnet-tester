from ipaddress import ip_address
import socket

dest_ip = "2.155.190.111"
dest_port = 6454


def open_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.0)  # in secs
    sock.bind(("0.0.0.0", 6454))
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
