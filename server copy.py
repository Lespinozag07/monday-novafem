from flask import Flask

app = Flask("Python-Server")

#endpoint 1
@app.route('/hello' , methods=['GET'])
def function_hello():
    return "Hello beach"

#endpoint 2
@app.route('/bye' , methods=['GET'])
def function_bye():
    return "Bye bye beach"

#run the server
app.run(port=3690);