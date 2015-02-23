#!/usr/bin/python
import server
import config

def main(server_class=server.MultiThreadedHTTPServer, handler_class=server.RequestHandler):
    # set up the server socket based on values in config.py
    server_address = (config.address, config.port)
    # create the server object bound to the server socket
    httpd = server_class(server_address, handler_class)
    try:
        # start the server
        httpd.serve_forever()
    except:
        print "Stopping..."
        # stop the server on error or keyboard interrupt
        httpd.shutdown()

if __name__ == "__main__":
    # if we are running this file directly (not importing)
    # then run the main() function
    main()

