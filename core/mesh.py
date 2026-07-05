import socket
import threading
import time
import json
import struct

DISCOVERY_PORT = 6969
MCAST_GRP = "239.255.255.250"
PORT_RANGE = range(6970, 7000)


class SwarmMesh:
    def __init__(self, node):
        self.node = node
        self.peers = {}
        self.port = None
        self.running = True
        self.message_callbacks = []
        self._msg_sock = None
        self._disc_sock = None
        self._discovery_ok = False

        self._start_sockets()

        threading.Thread(target=self._broadcast, daemon=True).start()
        threading.Thread(target=self._listen_discovery, daemon=True).start()
        threading.Thread(target=self._listen_messages, daemon=True).start()

    def register_callback(self, callback):
        self.message_callbacks.append(callback)

    def _get_local_ip(self):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            ip = probe.getsockname()[0]
            probe.close()
            return ip
        except OSError:
            return None

    def _bind_message_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for port in PORT_RANGE:
            try:
                sock.bind(("", port))
                sock.settimeout(3)
                self.port = port
                return sock
            except OSError:
                continue
        sock.bind(("", 0))
        sock.settimeout(3)
        self.port = sock.getsockname()[1]
        return sock

    def _start_sockets(self):
        self._msg_sock = self._bind_message_socket()

        self._disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._disc_sock.bind(("", DISCOVERY_PORT))
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            self._disc_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self._disc_sock.settimeout(3)
            self._discovery_ok = True
        except OSError as exc:
            print(f"\x1b[31mDiscovery socket failed on UDP {DISCOVERY_PORT}: {exc}\x1b[0m")

        local_ip = self._get_local_ip() or "unknown"
        print(
            f"\x1b[33mMesh up — node {self.node.node_id} | "
            f"messages UDP {self.port} | discovery UDP {DISCOVERY_PORT} | local {local_ip}\x1b[0m"
        )
        print(
            f"\x1b[90mFirewall: allow inbound UDP {self.port} and {DISCOVERY_PORT} "
            f"on Private networks.\x1b[0m"
        )

    def _get_broadcast_targets(self):
        targets = [
            (MCAST_GRP, DISCOVERY_PORT),
            ("255.255.255.255", DISCOVERY_PORT),
            ("127.0.0.1", DISCOVERY_PORT),
        ]
        local_ip = self._get_local_ip()
        if local_ip:
            parts = local_ip.split(".")
            if len(parts) == 4:
                targets.append((f"{parts[0]}.{parts[1]}.{parts[2]}.255", DISCOVERY_PORT))
        return targets

    def _handle_presence(self, msg, addr):
        peer_id = msg.get("node_id")
        peer_port = msg.get("port")
        if not peer_id or peer_id == self.node.node_id or not peer_port:
            return

        peer_addr = msg.get("host") or addr[0]
        if peer_addr in ("127.0.0.1", "0.0.0.0"):
            peer_addr = addr[0]

        is_new = peer_id not in self.peers
        self.peers[peer_id] = {
            "last_seen": time.time(),
            "addr": peer_addr,
            "port": peer_port,
        }
        if is_new:
            self.node.note_peer(peer_id)
            print(f"\x1b[32m✓ Discovered: {peer_id} at {addr[0]}:{peer_port}\x1b[0m")

    def _listen_discovery(self):
        if not self._discovery_ok:
            return

        while self.running:
            try:
                data, addr = self._disc_sock.recvfrom(2048)
                msg = json.loads(data.decode("utf-8", errors="ignore"))
                if msg.get("type") == "presence":
                    self._handle_presence(msg, addr)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                pass

    def _listen_messages(self):
        while self.running:
            try:
                data, addr = self._msg_sock.recvfrom(2048)
                msg = json.loads(data.decode("utf-8", errors="ignore"))
                if msg.get("type") == "private_message":
                    if msg.get("from") == self.node.node_id:
                        continue
                    for cb in self.message_callbacks:
                        cb(msg)
                elif msg.get("type") == "presence":
                    self._handle_presence(msg, addr)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                pass

    def _broadcast(self):
        while self.running:
            try:
                msg = {
                    "type": "presence",
                    "node_id": self.node.node_id,
                    "port": self.port,
                    "host": self._get_local_ip(),
                }
                payload = json.dumps(msg).encode()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                for target, port in self._get_broadcast_targets():
                    try:
                        sock.sendto(payload, (target, port))
                    except OSError:
                        pass
                sock.close()
            except OSError:
                pass
            time.sleep(5)

    def send_private_message(self, target_id: str, content: str, source: str = "human"):
        if target_id not in self.peers:
            print(f"\x1b[31mNode {target_id} not found. Try /nodes\x1b[0m")
            return

        try:
            payload = {
                "type": "private_message",
                "from": self.node.node_id,
                "content": content,
                "source": source,
            }
            peer = self.peers[target_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(json.dumps(payload).encode(), (peer["addr"], peer["port"]))
            sock.close()
            print(f"\x1b[32m→ Sent to {target_id} at {peer['addr']}:{peer['port']}\x1b[0m")
        except Exception as e:
            print(f"\x1b[31mSend failed: {e}\x1b[0m")

    def peer_status(self):
        if not self.peers:
            return "None yet"
        lines = []
        for peer_id, info in self.peers.items():
            lines.append(f"{peer_id} @ {info['addr']}:{info['port']}")
        return "\n  ".join(lines)