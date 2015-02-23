class page():
    def __init__(self, server, form):
        self.response = 404
        self.headers = {"Content-Type": "text/html"}
        self.content = "<html>404 Not found</html>"
