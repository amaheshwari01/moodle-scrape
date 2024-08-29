import json
from flask import Flask, Response, request, jsonify
import scrape
from flask_cors import CORS, cross_origin
from waitress import serve
import base64
import os
from cryptography.fernet import Fernet


apikey = bytes(os.environ["MY_KEY"], "utf-8")

app = Flask(__name__)
CORS(app)


def sessionToCOokies(session):
    cookies = session.cookies.get_dict()

    # Add expiry dates to cookies
    for cookie in session.cookies:
        cookies[cookie.name] = {
            "value": cookie.value,
            "expires": str(cookie.expires),
            "domain": cookie.domain,
        }
    return cookies


@app.route("/")
def hello():
    return "Hello World"


@app.route("/login", methods=["POST"])
@cross_origin()
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    if not username or not password:
        return jsonify({"message": "please give valid body"}), 400
    try:
        session = scrape.create_session(username, password)
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    return jsonify({"cookies": sessionToCOokies(session)})


@app.route("/getClasses", methods=["POST"])
@cross_origin()
def classes():
    cookies = request.json.get("cookies")
    username = request.json.get("username")
    password = request.json.get("password")
    # print("requestmade")
    if not username or not password:
        return jsonify({"message": "please give valid body"}), 400
    try:
        session = scrape.regenSession(username, password, cookies)
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    classes = scrape.getclasses(session)
    return jsonify({"classes": classes, "cookies": sessionToCOokies(session)})


@app.route("/getCourseData", methods=["POST"])
@cross_origin()
def coursedata():
    cookies = request.json.get("cookies")
    username = request.json.get("username")
    password = request.json.get("password")
    courseurl = request.json.get("courseurl")
    if not username or not password or not courseurl:
        return jsonify({"message": "please give valid body"}), 400
    try:
        session = scrape.regenSession(username, password, cookies)
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    courseData = scrape.courseData(session, courseurl)
    return jsonify({"courseData": courseData, "cookies": sessionToCOokies(session)})


@app.route("/getLessonplan", methods=["POST"])
@cross_origin()
def getLessonplan():
    cookies = request.json.get("cookies")
    username = request.json.get("username")
    password = request.json.get("password")
    lessonurl = request.json.get("lessonurl")
    if not username or not password or not lessonurl:
        return jsonify({"message": "please give valid body"}), 400

    try:
        session = scrape.regenSession(username, password, cookies)
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    try:
        lessonpan = scrape.getDayPlan(lessonurl, session, cookies, username, password)
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    return lessonpan


@app.route("/showPage/<path:url>", methods=["GET"])
@cross_origin()
def showPage(url):
    # return request.args.to_dict()

    data = request.args.get("auth")
    cipher_suite = Fernet(apikey)

    data = cipher_suite.decrypt(str(data))
    # print(data)
    decoded_string = base64.b64decode(data)
    data = json.loads(decoded_string)
    try:
        cookies = data["cookies"]
        username = data["username"]
        password = data["password"]
        # get all params except auth
        params = request.args.to_dict()
        del params["auth"]
        paramstring = "?"
        for key in params:
            paramstring += key + "=" + params[key] + "&"
        paramstring = paramstring[:-1]
        url = "https://learn.vcs.net/" + url + paramstring
        # return url
    except Exception as e:
        return jsonify({"message": "please give valid body"}), 400
    # # url
    try:
        session = scrape.regenSession(username, password, cookies)
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    return scrape.getPage(url, session, cookies, username, password)


def run():
    serve(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    run()
    # app.run(debug=True, port=8090)
