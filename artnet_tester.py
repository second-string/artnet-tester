from ipaddress import ip_address

import helpers

from artnet_packet_tx import ArtPollPacket, ArtProgIpPacket, ArtCommandPacket, ArtDmxPacket
from artnet_packet_rx import ArtPollReplyPacket, ArtIpProgReplyPacket

if __name__ == "__main__":
    print("Art-Net packet tester")

    helpers.choose_interface_at_startup()
    sock = helpers.open_connection()

    discovered_devices = []
    selected_ips = []
    selected_universes = [0]

    while True:
        print()
        print(
            f"Bound to {helpers.bound_local_ip} on {helpers.bound_iface} (subnet broadcast {helpers.bound_broadcast})"
        )
        print(
            f"Selected devices: {selected_ips if selected_ips else '(none)'}")
        print(f"Selected universes: {selected_universes}")
        print()
        print("Device options:")
        print("1)  Scan for ArtNodes")
        print("2)  Select devices from discovered")
        print("3)  Manually select IP")
        print("4)  Deselect devices")
        print("5)  Select universe(s) to send to")

        print("ArtNet options:")
        print("6)  Send ArtPoll")
        print("7)  Send ArtIPProg")
        print("8)  Send ArtCommand")
        print("9)  Send ArtDMX")
        print("10) Send static ArtDMX (full universe of one byte value)")
        print("11) Send cycling RGB ArtDMX (ctrl+c or any key to stop)")
        print("12) Send cycling RGBW ArtDMX (ctrl+c or any key to stop)")
        print("13) Exit")
        print()

        num = helpers.prompt_for_number_in_range("Choice: ", range(1, 14))

        if num == 1:
            print("Scanning...")
            discovered_devices = helpers.scan_for_artnodes(sock)
            print(f"Discovered {len(discovered_devices)} device(s):")
            helpers.print_discovered(discovered_devices)

        elif num == 2:
            if not discovered_devices:
                print("No discovered devices. Run a scan first (menu 1).")
                continue
            print("Discovered devices:")
            helpers.print_discovered(discovered_devices)
            print("Enter row numbers, IPs (space-delimited), or 'all'.")
            raw = input("Select: ").strip()
            source_ips = [d['ip'] for d in discovered_devices]
            if raw.lower() == "all":
                to_add = source_ips
            else:
                to_add, ok = helpers.parse_selection_tokens(raw, source_ips)
                if not ok:
                    continue
            added = 0
            for ip in to_add:
                if ip not in selected_ips:
                    selected_ips.append(ip)
                    added += 1
            print(f"Added {added} device(s). Selected: {selected_ips}")

        elif num == 3:
            ip = helpers.prompt_for_ip("IP to add: ")
            ip_str = str(ip)
            if not helpers.ip_in_bound_subnet(ip_str):
                print(
                    f"IP {ip_str} is not in the bound subnet "
                    f"({helpers.bound_local_ip}/{helpers.bound_netmask}). Rejected."
                )
                continue
            if ip_str in selected_ips:
                print(f"{ip_str} already in selected list")
            else:
                selected_ips.append(ip_str)
                print(f"Added {ip_str}. Selected: {selected_ips}")

        elif num == 4:
            if not selected_ips:
                print("Nothing to deselect")
                continue
            print("Currently selected:")
            helpers.print_selected(selected_ips)
            print("Enter row numbers, IPs (space-delimited), or 'all'.")
            raw = input("Deselect: ").strip()
            if raw.lower() == "all":
                selected_ips = []
                print("Cleared selection")
                continue
            to_remove, ok = helpers.parse_selection_tokens(
                raw, list(selected_ips))
            if not ok:
                continue
            for ip in to_remove:
                if ip in selected_ips:
                    selected_ips.remove(ip)
            print(f"Selected: {selected_ips if selected_ips else '(none)'}")

        elif num == 5:
            print("Enter space-delimited list of universes (0-32767).")
            selected_universes = helpers.prompt_for_numbers_in_range(
                "Universes: ", range(0, 32768))
            print(f"Selected universes: {selected_universes}")

        elif num == 6:
            if not selected_ips:
                print("No devices selected")
                continue
            for ip in selected_ips:
                print(f"-> ArtPoll to {ip}")
                packet = ArtPollPacket()
                raw_byte_response = helpers.send_packet(packet, sock, ip, True)
                if not raw_byte_response:
                    print("Timed out waiting for response")
                else:
                    reply_packet = ArtPollReplyPacket(raw_byte_response)
                    reply_packet.print_fields()

        elif num == 7:
            if not selected_ips:
                print("No devices selected")
                continue
            print()
            print("Select the field to program")
            print("1) Set IP address")
            print("2) Set default gateway")
            print("3) Set subnet mask")
            print("4) Set port")
            print("5) Set DHCP or static IP")
            print("6) No changes, read existing config")
            print()

            sub = helpers.prompt_for_number_in_range("Choice: ", range(1, 7))
            packet = ArtProgIpPacket()
            if sub == 1:
                ip = helpers.prompt_for_ip("New IP: ")
                packet.set_new_ip(ip)
            elif sub == 2:
                gateway = helpers.prompt_for_ip("New default gateway: ")
                packet.set_new_gateway(gateway)
            elif sub == 3:
                subnet = helpers.prompt_for_ip("New subnet mask: ")
                packet.set_new_subnet_mask(subnet)
            elif sub == 4:
                port = helpers.prompt_for_number("New port: ")
            elif sub == 5:
                ip_mode = helpers.prompt_for_string_in_range(
                    "DHCP or static? (dhcp/static): ", ["dhcp", "static"])
                packet.set_dhcp(ip_mode.lower() == "dhcp")
            elif sub == 6:
                pass

            for target_ip in selected_ips:
                print(f"-> ArtIPProg to {target_ip}")
                raw_byte_response = helpers.send_packet(
                    packet, sock, target_ip, True)
                if not raw_byte_response:
                    print("Timed out waiting for response")
                else:
                    reply_packet = ArtIpProgReplyPacket(raw_byte_response)
                    reply_packet.print_fields()

        elif num == 8:
            if not selected_ips:
                print("No devices selected")
                continue
            command_string = input("Enter the command string: ")
            packet = ArtCommandPacket(command_string)
            for ip in selected_ips:
                helpers.send_packet(packet, sock, ip, False)
            print(f"Sent ArtCommand to {selected_ips}")

        elif num == 9:
            if not selected_ips:
                print("No devices selected")
                continue
            print("Enter DMX data bytes (1-512 bytes, space-delimited).")
            print("Use decimal (e.g. 255) or hex with 0x prefix (e.g. 0xFF).")
            data_bytes = None
            while data_bytes is None:
                raw = input("Data: ").strip()
                tokens = raw.split()
                if len(tokens) < 1 or len(tokens) > 512:
                    print(f"Must enter 1-512 bytes, got {len(tokens)}")
                    continue
                parsed = []
                error = False
                for token in tokens:
                    try:
                        if token.lower().startswith("0x"):
                            val = int(token, 16)
                        else:
                            val = int(token)
                        if val < 0 or val > 255:
                            print(f"Value {token} out of range (0-255)")
                            error = True
                            break
                        parsed.append(val)
                    except ValueError:
                        print(f"Invalid value: {token}")
                        error = True
                        break
                if not error:
                    data_bytes = parsed
            for universe in selected_universes:
                packet = ArtDmxPacket(universe, data_bytes)
                for ip in selected_ips:
                    helpers.send_packet(packet, sock, ip, False)
            print(
                f"Sent ArtDMX to {selected_ips} on universes {selected_universes}, {len(data_bytes)} byte(s)"
            )

        elif num == 10:
            if not selected_ips:
                print("No devices selected")
                continue
            byte_val = helpers.prompt_for_number_in_range(
                "Byte value (0-255): ", range(0, 256))
            data_bytes = [byte_val] * 512
            for universe in selected_universes:
                packet = ArtDmxPacket(universe, data_bytes)
                for ip in selected_ips:
                    helpers.send_packet(packet, sock, ip, False)
            print(
                f"Sent ArtDMX to {selected_ips} on universes {selected_universes}, 512 bytes of {byte_val}"
            )

        elif num == 11:
            if not selected_ips:
                print("No devices selected")
                continue
            print(
                f"Cycling R -> G -> B on {selected_ips} × {selected_universes}. Press any key to stop."
            )
            colors = [("R", 0), ("G", 1), ("B", 2)]
            idx = 0
            try:
                while True:
                    label, offset = colors[idx]
                    data_bytes = [0] * 512
                    for i in range(offset, 510, 3):
                        data_bytes[i] = 128
                    for universe in selected_universes:
                        packet = ArtDmxPacket(universe, data_bytes)
                        for ip in selected_ips:
                            helpers.send_packet(packet, sock, ip, False)
                    print(f"Sent {label}=128")
                    if helpers.wait_or_key_pressed(1.0):
                        break
                    idx = (idx + 1) % len(colors)
            except KeyboardInterrupt:
                print()
            print("Stopped RGB cycle")

        elif num == 12:
            if not selected_ips:
                print("No devices selected")
                continue
            print(
                f"Cycling R -> G -> B -> W on {selected_ips} × {selected_universes}. Press any key to stop."
            )
            colors = [("R", 0), ("G", 1), ("B", 2), ("W", 3)]
            idx = 0
            try:
                while True:
                    label, offset = colors[idx]
                    data_bytes = [0] * 512
                    for i in range(offset, 512, 4):
                        data_bytes[i] = 128
                    for universe in selected_universes:
                        packet = ArtDmxPacket(universe, data_bytes)
                        for ip in selected_ips:
                            helpers.send_packet(packet, sock, ip, False)
                    print(f"Sent {label}=128")
                    if helpers.wait_or_key_pressed(1.0):
                        break
                    idx = (idx + 1) % len(colors)
            except KeyboardInterrupt:
                print()
            print("Stopped RGBW cycle")

        elif num == 13:
            break

    sock.close()
