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
        cookies[cookie.name] = {
            "value": cookie.value,
            "expires": str(cookie.expires),
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
    lessonpan = scrape.getDayPlan(lessonurl, session)
    return lessonpan


def run():
    serve(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    # run()
    app.run(debug=True)
