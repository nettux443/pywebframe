class page():
    def __init__(self, server, form):
        self.response = 200
        self.headers = {"Content-Type": "text/html"}
        content = ""
        content += "<html>"
        content += "<head>"
        content += "<title>Example Page</title>"
        content += "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/main.css\" />"
        content += "</head>"
        content += "<body>"
        content += "<h1>This is an example page</h1>"
        content += "</body>"
        content += "</html>"
        self.content = content
