from flask import Flask
import requests
import os

app = Flask(__name__)

@app.route("/")
def handler():
    print("serving container received a request.")
    response = requests.get("http://127.0.0.1:8080")
    return response.text

if __name__ == "__main__":
    print("serving container started...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))

