import json
from datetime import datetime
from urllib import parse

import requests
from bs4 import BeautifulSoup


def get_course(href):
    course_id = parse.parse_qs(parse.urlsplit(href).query)["content"]
    return course_id[0][4:-3]


# Set headers
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})

# Get the first page of search results
# TODO: Make this url specifiable at runtime
url = "https://lsa.umich.edu/cg/cg_results.aspx?termArray=f_20_2310&cgtype=ug&show=20&department=EECS&iPageNum=1"
req = requests.get(url, headers)
soup = BeautifulSoup(req.content, "html5lib")

courses = {}

flag = True
while flag:
    for div in soup.find_all("div", {"class": "ClassRow"}):
        course = get_course(div["data-url"])
        if course not in courses:
            course_url = "https://lsa.umich.edu/cg/" + div["data-url"]
            course_req = requests.get(course_url, headers)
            course_soup = BeautifulSoup(course_req.content, "html5lib")

            print(course_url)


            # # print(course_soup.select(".clsschedulerow > div > div:first-child"))
            # for section in course_soup.select(".clsschedulerow > div > div:first-child"):
            #     print(section)
            #     if section.contents[1].string:
            #         print(str(section.contents[1].string.encode('utf-8')))
            #         # print({ "os" : section.contents[4].string, "ors" : section.contents[5].string, "wl" : section.contents[6].string})

            course_dict = {"os": 0, "ors": 0, "wl": 0}

            for section in course_soup.find_all("div", {"class": "clsschedulerow"}):
                row = section.div.div
                row_values = [x for x in row.stripped_strings]


                if str(row_values[3]) == "P":
                    last_value = ""
                    for value in row_values:
                        if last_value == "Open Seats:":
                            if value.isnumeric():
                                course_dict["os"] += int(value)
                        elif last_value == "Open Restricted Seats:":
                            if value.isnumeric():
                                course_dict["ors"] += int(value)
                        elif last_value == "Wait List:":
                            if value.isnumeric():
                                course_dict["wl"] += int(value)
                                break

                        last_value = value

                # if "LEC" in str(blah.div.div.div.span.string.encode('utf-8')):
                #     print(blah)

            courses[course] = course_dict
            print(course_dict)
            # flag = False
            # break
    # break

    next_a = soup.find("a", {"id": "contentMain_hlnkNextTop"})
    if next_a is None:
        break

    next_req = requests.get("https://lsa.umich.edu/cg/" + next_a["href"], headers)
    soup = BeautifulSoup(next_req.content, "html5lib")

print("Done scraping")

timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

with open(timestamp + ".json", "w") as fp:
    json.dump(courses, fp)