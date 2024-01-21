from flask import Flask, request, jsonify
import scrape
from flask_cors import CORS, cross_origin
from waitress import serve


app = Flask(__name__)
CORS(app)


def sessionToCOokies(session):
    cookies = session.cookies.get_dict()

    # Add expiry dates to cookies
    for cookie in session.cookies:
        # print(cookie)
        cookies[cookie.name] = {
            "value": cookie.value,
            "expires": cookie.expires,
            "domain": cookie.domain,
        }
    return cookies


@app.route("/getClasses", methods=["POST"])
@cross_origin()
def classes():
    cookies = request.json.get("cookies")
    username = request.json.get("username")
    password = request.json.get("password")
    print("requestmade")
    if not username or not password:
        return jsonify({"message": "please give valid body"}), 400
    session = scrape.regenSession(username, password, cookies)

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

    session = scrape.regenSession(username, password, cookies)
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

    session = scrape.regenSession(username, password, cookies)
    lessonpan = scrape.getDayPlan(lessonurl, session)
    return lessonpan


if __name__ == "__main__":
    print("running")
    serve(app, host="0.0.0.0", port=1257)