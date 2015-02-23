class page():
    def __init__(self, server, form):
        self.response = 200
        self.headers = {"Content-Type": "text/html"}
        content = ""
        content += "<html>"
        content += "<head>"
        content += "<title>Hello World</title>"
        content += "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/main.css\" />"
        content += "</head>"
        content += "<body>"
        content += "Hello, world!"
        content += "</body>"
        content += "</html>"
        self.content = content
