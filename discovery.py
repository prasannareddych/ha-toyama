import asyncio
import logging
import socket
import struct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeshDiscovery:
    def __init__(self):
        self.socket = None

    async def parse_mdns_packet(self, payload):
        def parse_mdns_name(payload, offset):
            labels = []
            while True:
                length = payload[offset]
                if length == 0:
                    offset += 1
                    break
                if (length & 0xC0) == 0xC0:
                    pointer = struct.unpack(
                        "!H", payload[offset:offset + 2])[0]
                    offset += 2
                    pointer_offset = pointer & 0x3FFF
                    labels.append(parse_mdns_name(payload, pointer_offset)[0])
                    break
                else:
                    offset += 1
                    labels.append(payload[offset:offset + length].decode())
                    offset += length
            return ".".join(labels), offset

        def parse_txt_records(data):
            txt_records = []
            offset = 0
            while offset < len(data):
                length = data[offset]
                offset += 1
                txt_record = data[offset:offset + length].decode()
                txt_records.append(txt_record)
                offset += length
            return txt_records

        def parse_mdns_record(payload, offset):
            name, offset = parse_mdns_name(payload, offset)
            record_type = struct.unpack(">H", payload[offset:offset + 2])[0]
            record_class = struct.unpack(
                ">H", payload[offset + 2:offset + 4])[0]
            ttl = struct.unpack(">I", payload[offset + 4:offset + 8])[0]
            data_length = struct.unpack(
                ">H", payload[offset + 8:offset + 10])[0]
            data_offset = offset + 10
            data = payload[data_offset:data_offset + data_length]
            offset = data_offset + data_length

            record_data = None
            if record_type == 16:  # TXT record
                record_data = parse_txt_records(data)

            return {
                "name": name,
                "type": record_type,
                "class": record_class,
                "ttl": ttl,
                "data_length": data_length,
                "data": record_data
            }, offset

        def parse_mdns_answers(payload, offset, num_answers):
            answers = []
            for _ in range(num_answers):
                answer, offset = parse_mdns_record(payload, offset)
                answers.append(answer)
            return answers, offset

        def parse_mdns_payload(payload):
            tid = struct.unpack('>H', payload[0:2])[0]
            flags = struct.unpack(">H", payload[2:4])[0]
            questions = struct.unpack(">H", payload[4:6])[0]
            answers_count = struct.unpack(">H", payload[6:8])[0]
            auth_rrs = struct.unpack(">H", payload[8:10])[0]
            addt_rrs = struct.unpack(">H", payload[10:12])[0]

            offset = 12
            answers, offset = parse_mdns_answers(
                payload, offset, answers_count)

            return {
                "tid": f"0x{tid:04X}",
                "flags": f"0x{flags:04X}",
                "questions": questions,
                "answers_count": answers_count,
                "auth_rrs": auth_rrs,
                "addt_rrs": addt_rrs,
                "answers": answers
            }

        info = parse_mdns_payload(payload)
        for i in info['answers']:
            if i.get('type') == 16:  # type TXT
                return dict(item.split('=') for item in i['data'])

    async def send_mdns_packet(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        multicast_ip = '224.0.0.251'
        port = 5353
        query = (
            b'\x00\x00'          # Transaction ID
            b'\x01\x00'          # Flags (Standard Query)
            b'\x00\x01'          # Questions (1)
            b'\x00\x00'          # Answer RRs (0)
            b'\x00\x00'          # Authority RRs (0)
            b'\x00\x00'          # Additional RRs (0)
            b'\x07\x5f\x74\x6f\x79\x61\x6d\x61'  # _toyama
            b'\x04\x5f\x74\x63\x70'  # _tcp
            b'\x05\x6c\x6f\x63\x61\x6c'  # _local
            b'\x00'             # Null terminator for FQDN
            b'\x00\x0c'         # QTYPE (PTR)
            b'\x00\x01'         # QCLASS (IN)
        )
        self.socket.sendto(query, (multicast_ip, port))
        logger.debug("Sent mDNS query packet")

    async def discover(self):
        await self.send_mdns_packet()
        loop = asyncio.get_event_loop()
        self.socket.settimeout(10)
        while True:
            try:
                data, addr = await loop.run_in_executor(None, self.socket.recvfrom, 1024)
                info = await self.parse_mdns_packet(data)
                if 'Serial' in info.keys():
                    info['host'] = addr[0]
                    return addr[0], info
            except asyncio.TimeoutError:
                raise MeshNotFoundError(f"No mesh device found")
            except:
                pass


async def discover():
    discovery = MeshDiscovery()
    logger.debug("running discovery")
    mesh, mesh_info = await discovery.discover()
    logger.info(f"discovered: {mesh}")
    logger.debug(f"mesh_info: {mesh_info}")
    return mesh


class MeshNotFoundError(Exception):
    """Mesh Not Found Exception"""
