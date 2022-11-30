import argparse
import asyncio
import logging
import mimetypes
import os
import socket
from datetime import datetime
from http import HTTPStatus
from urllib.parse import urlparse, unquote_plus

from asyncio_pool import AioPool

SERVER_NAME = "SimpleHTTPServer"
SERVER_VERSION = "1.0"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = "8080"
DEFAULT_WORKERS_NUM = 4

DEFAULT_DOC_ROOT = "."
DEFAULT_LOGFILE_PATH = "./.tmp/logs/logs.txt"
DEFAULT_ENCODING = "utf-8"
DEFAULT_CONTENT_TYPE = "application/json"

HTTP_PROTOCOL = "HTTP/1.1"
BUF_SIZE = 1024
ASYNCIO_WAIT_TIMEOUT = 5
DATE_FORMAT_STRING = "%a, %d %b %Y %H:%M:%S GMT"
INDEX_FILE_NAME = "index.html"

RN = "\r\n"
RNRN = RN * 2

GET_METHOD = "GET"
ALLOWED_METHODS = [GET_METHOD, "HEAD"]


def close_conn(conn: socket.socket):
    """
    TODO
    :param conn:
    :return:
    """
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()


class SimpleHTTPHandler:
    def __init__(self, doc_root):
        """
        TODO
        """
        self.response = ""
        self.method = ""

        self.doc_root = doc_root
        self.path_to_file = ""

        self.headers = {
            "Content-Type": DEFAULT_CONTENT_TYPE,
            "Content-Length": "0",
            "Server": f"{SERVER_NAME}/{SERVER_VERSION}",
            "Connection": "close",
            "Date": datetime.now().strftime(DATE_FORMAT_STRING),
        }

    def parse_request(self, request):
        """
        TODO
        :param request:
        :return:
        """
        try:
            request_parts = request.split(RN)
            method, qs, protocol = request_parts[0].split()
            logging.info(f"Parsing request: {request_parts[0]}")
        except ValueError:
            return HTTPStatus.BAD_REQUEST

        if method not in ALLOWED_METHODS:
            return HTTPStatus.METHOD_NOT_ALLOWED

        self.method = method

        path_from_url = unquote_plus(urlparse(qs).path)
        path_to_file = self.doc_root + path_from_url

        # Deny /../../../ cases:
        if not os.path.abspath(path_to_file).startswith(os.path.abspath(self.doc_root)):
            return HTTPStatus.BAD_REQUEST

        if os.path.isfile(path_to_file):
            self.path_to_file = path_to_file
        elif path_to_file.endswith(os.sep) and os.path.isfile(
            os.path.join(path_to_file, INDEX_FILE_NAME)
        ):
            self.path_to_file = os.path.join(path_to_file, INDEX_FILE_NAME)

        if self.path_to_file:
            return HTTPStatus.OK
        else:
            return HTTPStatus.NOT_FOUND

    def get_response(self, request: str):
        """
        TODO
        :param request:
        :return:
        """
        code = self.parse_request(request)
        response_parts = [f"{HTTP_PROTOCOL} {int(code)} {code.phrase}"]
        body = ""
        if code == HTTPStatus.OK:
            mtype, _ = mimetypes.guess_type(self.path_to_file)
            if mtype:
                self.headers["Content-Type"] = mtype

            fsize = os.path.getsize(self.path_to_file)
            self.headers["Content-Length"] = str(fsize)

            if self.method == GET_METHOD:
                logging.info(f"Reading file: {self.path_to_file}")
                with open(self.path_to_file, "rb") as f:
                    body = f.read(fsize)

        response_parts += [": ".join(item) for item in self.headers.items()]
        self.response = (RN.join(response_parts) + RNRN).encode(DEFAULT_ENCODING)

        if body:
            self.response += body

        return self.response


async def handle_request(client, doc_root, loop):
    """
    TODO
    :param client:
    :param doc_root:
    :param loop:
    :return:
    """
    buf = b""
    while True:
        try:
            recv_task = asyncio.create_task(loop.sock_recv(client, BUF_SIZE))
            done, _ = await asyncio.wait(
                [recv_task],
                timeout=ASYNCIO_WAIT_TIMEOUT,
                return_when=asyncio.FIRST_COMPLETED,
            )
        except Exception as e:
            logging.exception("An error occurred while reading from socket")
            close_conn(client)
            return

        if not done or not next(iter(done)):
            break

        try:
            data = done.pop().result()
        except Exception as e:
            logging.exception("Error occurred while getting result from asyncio Future")

        buf += data

        if data.endswith(RNRN.encode(DEFAULT_ENCODING)):
            break

    request = buf.decode(DEFAULT_ENCODING)
    handler = SimpleHTTPHandler(doc_root)
    response = handler.get_response(request)
    try:
        await loop.sock_sendall(client, response)
    except Exception:
        logging.exception("Error occurred while sending response")
    close_conn(client)


class SimpleServer:
    def __init__(self, host, port, doc_root):
        """
        TODO
        """
        self.host = host
        self.port = port
        self.doc_root = doc_root

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.server.setblocking(False)

    def close(self):
        """
        TODO
        :return:
        """
        close_conn(self.server)

    async def start(self, workers_n):
        """
        TODO
        :param workers_n:
        :return:
        """
        loop = asyncio.get_event_loop()
        async with AioPool(size=workers_n, loop=loop) as pool:
            while True:
                client, _ = await loop.sock_accept(self.server)
                await pool.spawn(handle_request(client, self.doc_root, loop))


def main():
    parser = argparse.ArgumentParser(
        description="Simple HTTP Server",
    )
    parser.add_argument(
        "-i", "--ip", default=DEFAULT_HOST, help="Host address", metavar=""
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to listen",
        metavar="",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS_NUM,
        help="Number of workers to execute",
        metavar="",
    )
    parser.add_argument(
        "-r",
        "--doc_root",
        default=DEFAULT_DOC_ROOT,
        help="Path to documents root",
        metavar="",
    )
    parser.add_argument(
        "-l",
        "--log",
        default=DEFAULT_LOGFILE_PATH,
        help="Path to log file.",
        metavar="",
    )
    args = parser.parse_args()
    if args.log and not os.path.exists(os.path.dirname(args.log)):
        os.makedirs(os.path.dirname(args.log))

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    server = SimpleServer(args.ip, args.port, args.doc_root)

    try:
        logging.info(
            f"Simple Server has been started successfully at {args.ip}:{args.port}\n"
            f"Workers number: {args.workers}\n"
            f"Document root: {args.doc_root}\n"
        )
        asyncio.run(server.start(args.workers))
    except Exception as e:
        raise e
    finally:
        server.close()
        logging.info("Simple Server has been stopped")


if __name__ == "__main__":
    main()
