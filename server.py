import sys
import cgi
import os
import ssl
import datetime
import threading
import SocketServer
import BaseHTTPServer
import mimes, pages


class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    # Use a multithreaded server class to allow for concurrent access
    pass

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def read_in_chunks(self, file_object, chunk_size=55296):
        """Lazy function (generator) to read a file piece by piece.
        Default chunk size: 1k."""
        # Used to handle downloading of files too large to send in one response
        while True:
            # infinite loop
            try:
                # this block is expected to eventually error
                # read a chunk of data from the file stream
                data = file_object.read(chunk_size)
            except:
                # catch the error that we get when data runs out
                # then break out of the loop
                break
            # check if we got any data from the file on this loop
	    # this is belt and braces really
            if not data:
                # if not break the loop
                break

            # return  each chunk one at a time in series
            yield data

    def do_HEAD(self):
        # Override the BaseHTTPServer.do_HEAD method
        # this method is called for every HEAD request that we get
        page = self.path.split("/")[1]
        if not page:
            page = "index"

        if (os.path.isfile("pages/%s.py" % page) and hasattr(pages, page)) or os.path.isfile("static/" + self.path):
            # send an OK resonse code and an HTML Content Type
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
        else:
            # send a 404 not found response code
            self.send_response(404)

        # send the headers to the client
        self.end_headers()

    def do_GET(self):
        # Override the BaseHTTPServer.do_GET method
        # this method is called for every GET request that we get
        # get the first string after the hostname
        # subsequent strings (slash separated) can be used as parameters
        page = self.path.split("/")[1]
        # default to index if we just get '/' (or nothing)
        if not page:
            page = "index"

        # check for a dynamic handler that matches the page
        if self.dynamicPageExists(self.path):
            # we are serving a dynamic page
            # get a FieldStorage object containing POST and GET parameters
            form = cgi.FieldStorage(
                fp=self.rfile,
            )
            # initialize and store the appropriate page object
            page_obj = getattr(pages, page).page(self, form)
            # pass the page object to the serverPage method
            self.servePage(page_obj)
        elif os.path.exists("static/" + self.path):
            # If no dynamic handler was matched, check if a matching
            # static file exists under the static/ directory
            # get the actual path of the file to serve.
            # This is necassary in order to determine whether to list a
            # directory's contents, serve an index file or another file.
            # path will either become the path to the index file, remain
            # unchanged if it is already the path to a static file or
            # will be given a trailing slash to indicate a dir with no index
            path = self.staticPageExists(self.path)
            # a trailing slash means a dir with no index so list contents
            if path[-1] == "/":
                # list contents using the serveStaticDir method
                self.serveStaticDir(path)
            else:
                # serve a static file (maybe an index) using 
                # the serveStaticFile method
                self.serveStaticFile(path)
        else:
            # not found
            # serve the _catch catchall page.
            form = cgi.FieldStorage(
                # set the file pointer (fp) to the read stream
                fp=self.rfile,
            )
            # serve the catchall page by creating a page object
            # from the page._catch.page class and pass to the
            # servePage method
            self.servePage(pages._catch.page(self, form))

    def do_POST(self):
        # Override the BaseHTTPServer.do_POST method
        if self.dynamicPageExists(page):
            # we are serving a dynamic page
            # get the form of GET and POST parameters
            form = cgi.FieldStorage(
                # set the file pointer (fp) to the read stream
                fp=self.rfile, 
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
            })
            # dynamically create an instance of the correct page
            # class by getting the attribute of the pages module package
            # with the same name as the requested page then create an instance
            # the page class inside the attribute (which should be a module)
            self.servePage(getattr(pages, page).page(self, form))
        else:
            # makes no sense to post to static files so revert to GET
            self.do_GET()

    def servePage(self, page):
        # have we been passed a tuple of (response, headers, content)
        # or an actual page object
        if type(page) == type(tuple()):
            # if we have a tuple pull out the parts in order into 
            # appopriately named variables
            response = page[0]
            headers = page[1]
            content = page[2]
        else:
            # if we haven't got a tuple, assume it's a page object
            # and pull out it's attributes into local variables
            # appopriately named variables
            response = page.response
            headers = page.headers
            content = page.content

        # send our response code to the client
        self.send_response(response)
        # loop through the headers
        for header in headers.keys():
            # send each header, one by one.
            self.send_header(header, headers[header])

        # actually send the headers. After this we can only serve content
        self.end_headers()
        # write our content string to the wfile stream.
        self.wfile.write(content)

    def serveStaticDir(self, path):
        """
        This method takes a path to a directory as a string and
        serves a listing of the contents of the directory
        """
        # check that path string ends with a '/'
        if path[-1] != "/":
            # if path didn't end with a '/', make it.
            path = path + "/"
        # OK response code
        response = 200
        # MAKE ME CONFIGURABLE
        # send an html content type
        headers = {"Content-Type": "text/html"}
        # get a directory listing of the path
        # TODO: add error handling encase somehow we are given a
        # path that isn't a dir
        files = os.listdir("static" + path)
        # init content to an empty string
        content = ""
        # loop through the list of files
        for f in files:
            # trim leading slashes
            if f[0] == "/":
                # if we find a leading slash, slice from the 2nd char
                f = f[1:]

            # create a link html element and add it to the content string
            content += ("<a href='%s'>%s</a><br/>" % (path + f,f))

        # put the response, headers and content into a tuple and pass
        # to the servePage method
        self.servePage((response, headers, "<html>\n<head>\n<title>Dir list</title>\n</head>\n<body>\n<h1>Dir listing of %s</h1>\n%s</body>\n</html>\n" % (path.split("/")[-1], content)))


    def serveStaticFile(self, path):
        # serve static file
        # look for the file in the static dir
        filepath = "static/" +  path
        # TODO: add error handling here encase we get weird input
        # get the size of the file in bytes
        size = os.path.getsize(filepath)
        # is the file size over 1000 bytes?
        if size > 1000:
            # if so treat the file as BIG and serve in multiple responses
            ext = self.path.split("/")[-1].split(".")[-1].lower()
            if ext in mimes.types.keys():
                mime = mimes.types[ext]
            else:
                mime = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", size)
            self.send_header("Keep-Alive", "timeout=5, max=100")
            self.send_header("Connection", "Keep-Alive")
            self.end_headers()
            f = open(filepath)
            for data in self.read_in_chunks(f):
                self.wfile.write(data)

            f.close()
            # we're done here
            return

        # if the file was BIG we'd have left this method by now so from
        # this point downwards we know that the file is small (<1000B)
        # open a read-only file object pointing to the static file
        # we want to serve
        with open(filepath, 'r') as f:
            # read and store the contents in a variable
            content = f.read()
        # get the file extension of the file
        ext = self.path.split("/")[-1].split(".")[-1].lower()
        # do we know a mime type for that extension?
        # check the types dictionary in the mimes module (./mimes.py)
        if ext in mimes.types.keys():
            # if we know the mime type set the local var mimes to
            # the mime type string
            mime = mimes.types[ext]
        else:
            # otherwise default to plain text
            mime = "text/plain"

        # send an OK response
        response = 200
        # send the content type header with our mime type
        headers = {"Content-Type": mime}
        # serve the page as a tuple with the servePage method
        self.servePage((response, headers, content))


    def staticPageExists(self, path):
        """
        takes a path string
        returns False for non existant or the path to the file to be served
        eg for a dir will either return an index or a path ending with '/'
        for a path to an existing file (not dir) the file path will be
        returned as is.
        """
        if not os.path.exists("static/" + path):
            return False
        if not os.path.isdir("static/" + path):
            return path
        if os.path.isfile("static/" + path + "/index.html"):
            return path + "/index.html"
        if os.path.isfile("static/" + path + "/index.htm"):
            return path + "/index.htm"
        if path[-1] != "/":
            path = path + "/"
        return path

    def dynamicPageExists(self, path):
        # get the page name (after the first slash and before any others)
        # if we just hit '/' page will be empty
        page = self.path.split("/")[1]
        # if page is empty, change page to 'index'
        if not page: page = "index"
        # if a file exists in pages dir that matches the requested page (+.py)
        # and the pages module package has an attribute that has the same
        # name as the requested page, the page is deemed real
        if os.path.isfile("pages/%s.py" % page) and hasattr(pages, page):
            # so return True
            return True

        # if the page isn't real return False
        return False
