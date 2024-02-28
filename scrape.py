# create comments explaining the code
# use the requests library to get the html from the website
import base64
import json
import mimetypes
import os

from urllib.parse import urlparse
from urllib.parse import parse_qs
import urllib

from bs4 import BeautifulSoup
from pprint import pprint
from flask import Response, make_response
import requests
from markdownify import markdownify as md
import time
from cryptography.fernet import Fernet

apikey = bytes(os.environ["MY_KEY"], "utf-8")


start = time.time()
data = {}
blacklistClasses = [
    343,
    1252,
    1422,
    1301,
    385,
    920,
    1194,
    353,
    89,
    35,
    19,
    36,
    2,
    17,
    34,
    88,
    90,
    69,
    1202,
    1080,
]  # courses that show up but dont matter


def create_session(username, password):
    session = requests.Session()
    login_url = "https://learn.vcs.net/login/index.php"

    result = session.get(login_url)
    # print(result.text)

    soup = BeautifulSoup(result.text, "html.parser")
    token = soup.find("input", {"name": "logintoken"})["value"]
    payload = {
        "username": username,
        "password": password,
        "logintoken": token,
    }

    result = session.post(login_url, data=payload)
    if "Invalid login" in result.text:
        # print("Invalid Login")
        raise Exception("Invalid Login")
    return session


def getclasses(session):
    pass_url = "https://learn.vcs.net"

    r = session.get(pass_url)
    soup = BeautifulSoup(r.text, "html.parser")

    # print(r.text)
    # find ul with class unlist
    # find all li in ul
    # find all a in li
    classes = soup.find("ul", {"class": "unlist"})
    # print(soup.find("ul", {"class": "unlist"}))
    classes = classes.find_all("li")
    classes = [
        (c.find("a", href=True)["href"], c.find("a", href=True).text) for c in classes
    ]
    updatedclasses = []
    for c in classes:
        if int(c[0].split("id=")[1]) not in blacklistClasses:
            updatedclasses.append(c)
    classes = updatedclasses

    return classes


def authcheck(session):
    pass_url = "https://learn.vcs.net"

    r = session.get(pass_url)
    rdef = requests.get(pass_url)
    if r.text == rdef.text:
        return True
    else:
        return False


def regenSession(username, password, cookies):
    if not cookies:
        session = create_session(username, password)
        return session
    session = requests.Session()
    # put cookies into sesisin
    # session.
    curtime = time.time()
    for key in cookies.keys():
        # pprint(cookies[key])
        if cookies[key]["expires"] and cookies[key]["expires"] != "None":
            if curtime > int(cookies[key]["expires"]):
                try:
                    session = create_session(username, password)
                except Exception as e:
                    print(e)
                    raise Exception("Invalid Login")
                # print("expired")
                break

            cookie_obj = requests.cookies.create_cookie(
                domain=cookies[key]["domain"],
                name=key,
                value=cookies[key]["value"],
                expires=cookies[key]["expires"],
            )
        else:
            cookie_obj = requests.cookies.create_cookie(
                domain=cookies[key]["domain"],
                name=key,
                value=cookies[key]["value"],
            )

        session.cookies.set_cookie(cookie_obj)
    return session


def parse_class(classurl, session):
    curclass = session.get(classurl)
    curclasssoup = BeautifulSoup(curclass.text, "html.parser")
    sections = (
        curclasssoup.find("div", {"class": "tabs-wrapper"}).find("ul").find_all("li")
    )
    tabs = [
        (
            c.find("a", href=True).text.strip(),
            c.find("a", href=True)["href"].split("#")[0],
        )
        for c in sections
    ]

    # find a tab that says lesson and is case insensitive
    tabs = [t for t in tabs if "lesson" in t[0].lower()]
    LessonPlanPage = session.get(tabs[0][1])
    lpsoup = BeautifulSoup(LessonPlanPage.text, "html.parser")

    # pprint(lpsoup.find("div", {"class": "course-content"}))
    quarters = (
        lpsoup.find("div", {"class": "onetopic-tab-body"})
        .find("ul", {"class": "onetopic"})
        .find_all("a", href=True)
    )
    quarters = [
        (
            c["href"],
            c.text.split("Book")[0].strip(),
        )
        for c in quarters
    ]
    quarters = sorted(quarters)
    # pprint(quarters)
    # pprint( tabs[0][1])

    return quarters


def getLessonPlan(quarterurl, session):
    curquarter = session.get(quarterurl)
    curquartersoup = BeautifulSoup(curquarter.text, "html.parser")
    dayshtmls = curquartersoup.find("div", {"class": "card-body p-3"}).find_all("li")
    days = []
    for d in dayshtmls:
        curlink = d.find("a", href=True)
        curday = d.text
        if curlink is not None:
            curhref = curlink["href"]
            if curhref.startswith("http"):
                days.append([curhref, curday])
            else:
                days.append(["https://learn.vcs.net/mod/book/" + curhref, curday])
        else:
            days.append([quarterurl, curday])

    return days


def parseLinks(cursoup, cookies, username, password):
    for a_tag in cursoup.find_all("a"):
        # Check if 'href' contains "learn.vcs.net"
        if "learn.vcs.net" in a_tag.get("href", ""):

            data = {
                "cookies": cookies,
                "username": username,
                "password": password,
            }

            parsed_url = urlparse(a_tag["href"])
            params = parse_qs(parsed_url.query)

            # If you want a dictionary with single values instead of lists, you can do the following:
            params_single_values = {k: v[0] for k, v in params.items()}

            # print(params_single_values)
            paramstring = "?"
            for key in params_single_values:
                paramstring += key + "=" + params_single_values[key] + "&"
            try:
                cipher_suite = Fernet(apikey)

                encoded_text = urllib.parse.quote(
                    cipher_suite.encrypt(
                        bytes(
                            base64.b64encode(json.dumps(data).encode()).decode(),
                            "utf-8",
                        )
                    )
                )

                print(encoded_text)
                paramstring += "auth=" + encoded_text

            except Exception as e:
                print(e)
            # Replace 'href' with custom URL

            a_tag["href"] = (
                "https://moodle.aayanmaheshwari.com/showPage/"
                # "http://localhost:8090/showPage/"
                + parsed_url.path
                + paramstring
            )
    return cursoup


def getDayPlan(dayurl, session, cookies, username, password):
    curday = session.get(dayurl)

    curdaysoup = BeautifulSoup(curday.text, "html.parser")
    curdaysoup = parseLinks(curdaysoup, cookies, username, password)
    # replace all links with the href and the link contains learn.vcs.net with :
    if "book" in dayurl:
        dayplan = curdaysoup.find("div", {"class": "book_content"})
        # return str(dayplan)
        return str(dayplan)
    else:
        dayplan = curdaysoup.find("section", {"id": "region-main"}).find(
            "div", {"class": "no-overflow"}
        )
        return str(dayplan)

    # return plaindayplan


def getPage(url, session, cookies, username, password):
    # print(url)
    response = session.get(url)
    content_type = response.headers.get("content-type")
    content = response.content
    # if contenttype is html then parse links
    # if contettype is html or xml or php then parse links
    if "html" in content_type or "php" in content_type:
        content = parseLinks(
            BeautifulSoup(content, "html.parser"), cookies, username, password
        )
        content = str(content)

    return Response(content, content_type=content_type)


def courseData(session, classurl):
    data = {}
    quarters = parse_class(classurl, session)
    for q in quarters:
        data[q[1]] = {
            "id": q[0],
            "days": getLessonPlan(q[0], session),
        }
    data["id"] = classurl

    return data


# test scrape heree
if __name__ == "__main__":
    session = create_session("username", "password")
    classes = getclasses(session)

    for c in classes:
        try:
            quarters = parse_class(c[0])
            for q in quarters:
                print(q[1])

                data[c[1]][q[1]] = {
                    "id": q[0],
                    "days": getLessonPlan(q[0]),
                }

        except Exception as e:
            print("Invalid Class ")
            print(e)
    with open("data.json", "w") as f:
        json.dump(data, f)
    print(time.time() - start)
