import socket, time

HOST = "0.0.0.0"
PORT = 9999
BUF  = 2048

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    print(f"[BASE] UDP echo listening on {HOST}:{PORT}")
    while True:
        data, addr = s.recvfrom(BUF)       
        s.sendto(data, addr)                 

if __name__ == "__main__":
    main()
