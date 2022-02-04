import socket

if __name__ == "__main__":
    import sys
    
    assert len(sys.argv) > 1
    outfile = sys.argv[1]

    with open(outfile) as f:
        f.write(socket.gethostname())