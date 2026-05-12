from ipaddress import ip_address, IPv4Address, IPv4Network
import select
import socket
import sys
import termios
import time
import tty
import netifaces

DEST_PORT = 6454
IP_BOUND_IF = 25  # macOS socket option

bound_iface = None
bound_local_ip = None
bound_netmask = None
bound_broadcast = None


def _interface_priority(ip):
    first = int(ip.split(".")[0])
    if first == 2:
        return 0
    if first == 10:
        return 1
    return 2


def list_local_interfaces():
    """Return [(iface, ip, netmask), ...] for non-loopback IPv4 interfaces, sorted by priority."""
    out = []
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for addr_info in addrs:
            ip = addr_info.get('addr')
            netmask = addr_info.get('netmask')
            if not ip or ip.startswith("127."):
                continue
            out.append((iface, ip, netmask))
    out.sort(key=lambda t: (_interface_priority(t[1]), t[1]))
    return out


def choose_interface_at_startup():
    """Prompt the user to pick a local interface; record bound_* state and return (iface, ip, netmask)."""
    global bound_iface, bound_local_ip, bound_netmask, bound_broadcast
    ifaces = list_local_interfaces()
    if not ifaces:
        raise RuntimeError("No non-loopback IPv4 interfaces found")

    print()
    print("Available local interfaces:")
    for i, (iface, ip, netmask) in enumerate(ifaces, start=1):
        print(f"  {i}) {iface} {ip}/{netmask}")
    print()

    if len(ifaces) == 1:
        idx = 1
        print(
            f"Only one interface available; selecting {ifaces[0][0]} ({ifaces[0][1]})"
        )
    else:
        idx = prompt_for_number_in_range("Choose interface: ",
                                         range(1,
                                               len(ifaces) + 1))

    iface, ip, netmask = ifaces[idx - 1]
    bound_iface = iface
    bound_local_ip = ip
    bound_netmask = netmask
    bound_broadcast = str(
        IPv4Network(f"{ip}/{netmask}", strict=False).broadcast_address)
    return iface, ip, netmask


def open_connection():
    """Open a UDP socket bound to the previously-chosen interface."""
    if bound_iface is None:
        raise RuntimeError(
            "open_connection() called before choose_interface_at_startup()")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2.0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    if_index = socket.if_nametoindex(bound_iface)
    sock.setsockopt(socket.IPPROTO_IP, IP_BOUND_IF, if_index)
    sock.bind((bound_local_ip, 0))

    print(
        f"UDP socket bound to {bound_local_ip}:{DEST_PORT} on interface {bound_iface} (index {if_index})"
    )
    return sock


def ip_in_bound_subnet(ip_str):
    """True if ip_str falls inside the bound interface's subnet."""
    if bound_local_ip is None or bound_netmask is None:
        return False
    net = IPv4Network(f"{bound_local_ip}/{bound_netmask}", strict=False)
    return IPv4Address(ip_str) in net


def send(packet, sock, target_ip):
    sock.sendto(packet, (target_ip, DEST_PORT))


def wait_for_response(sock):
    try:
        data, address = sock.recvfrom(1024)
        return True, data
    except TimeoutError:
        print("Timed out waiting for response")
        return False, None


def send_packet(packet, sock, target_ip, expect_response):
    packet_bytes = packet.pack()
    send(packet_bytes, sock, target_ip)
    if expect_response:
        success, response = wait_for_response(sock)
        if success:
            return response


def scan_for_artnodes(sock):
    """Broadcast 3 ArtPolls 0.5s apart on the bound interface, collect unique responders.
    Returns list of dicts: [{'ip': str, 'short_name': str, 'long_name': str}, ...]
    """
    from artnet_packet_tx import ArtPollPacket
    from artnet_packet_rx import ArtPollReplyPacket

    poll_bytes = ArtPollPacket().pack()
    discovered = {}
    old_timeout = sock.gettimeout()
    sock.settimeout(0.1)

    try:
        scan_start = time.time()
        polls_sent = 0
        next_poll_at = scan_start
        # 3 polls every 0.5s = 1.5s of sending, then keep listening 0.5s after last poll
        scan_deadline = scan_start + 2.0

        while time.time() < scan_deadline:
            now = time.time()
            if polls_sent < 3 and now >= next_poll_at:
                sock.sendto(poll_bytes, (bound_broadcast, DEST_PORT))
                polls_sent += 1
                next_poll_at = now + 0.5
                print(f"  Sent ArtPoll {polls_sent}/3 to {bound_broadcast}")

            try:
                data, addr = sock.recvfrom(1024)
            except (TimeoutError, socket.timeout):
                continue

            try:
                reply = ArtPollReplyPacket(data)
                ip_str = str(IPv4Address(reply.ip_addr))
            except Exception:
                continue

            if ip_str not in discovered:
                discovered[ip_str] = {
                    'ip': ip_str,
                    'short_name': getattr(reply, 'port_name', ''),
                    'long_name': getattr(reply, 'long_name', ''),
                }
    finally:
        sock.settimeout(old_timeout)

    return list(discovered.values())


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


# Allows space-delimited list of input numbers
def prompt_for_numbers_in_range(prompt_text, allowed_values):
    while True:
        tokens = input(prompt_text).split()
        if not tokens:
            print("Must enter at least one number")
            continue
        parsed = []
        error = False
        for token in tokens:
            try:
                num = int(token)
                if num in allowed_values:
                    parsed.append(num)
                else:
                    print(f"Number {num} not in allowed values")
                    error = True
                    break
            except ValueError:
                print(f"Not a valid number: {token}")
                error = True
                break
        if not error:
            return parsed


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


def wait_or_key_pressed(timeout_sec):
    """Wait up to timeout_sec; return True if any key was pressed, False on timeout."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if ready:
            sys.stdin.read(1)
            return True
        return False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def print_discovered(discovered):
    if not discovered:
        print("(no devices discovered yet — run a scan)")
        return
    for i, dev in enumerate(discovered, start=1):
        name = dev.get('short_name') or dev.get('long_name') or ""
        print(f"  {i}) {dev['ip']:<15}  {name}")


def print_selected(selected_ips):
    if not selected_ips:
        print("(no devices selected)")
        return
    for i, ip in enumerate(selected_ips, start=1):
        print(f"  {i}) {ip}")


def parse_selection_tokens(raw, source_ips):
    """Parse space-delimited tokens against a snapshot of IPs.
    Each token is either a 1-based row index into source_ips or an IPv4 string.
    Returns (ips_chosen, ok). On error prints and returns (_, False)."""
    tokens = raw.strip().split()
    if not tokens:
        print("Must enter at least one selection")
        return [], False
    chosen = []
    for token in tokens:
        try:
            idx = int(token)
            if idx < 1 or idx > len(source_ips):
                print(f"Row {idx} out of range (1-{len(source_ips)})")
                return [], False
            chosen.append(source_ips[idx - 1])
            continue
        except ValueError:
            pass
        try:
            ip_address(token)
        except ValueError:
            print(f"Not a row number or valid IP: {token}")
            return [], False
        if token not in source_ips:
            print(f"IP {token} not in list")
            return [], False
        chosen.append(token)
    return chosen, True


def bswap16(val):
    return ((val & 0xFF) << 8) | ((val & 0xFF00) >> 8)


def bswap32(val):
    return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) | (
        (val & 0xFF0000) >> 8) | ((val & 0xFF000000) >> 24)


def uint32_to_big_endian_bytes(val):
    return [(val & 0xFF000000) >> 24, (val & 0x00FF0000) >> 16,
            (val & 0x0000FF00) >> 8, val & 0x000000FF]
