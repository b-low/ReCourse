import json
from datetime import datetime
from urllib import parse

import requests
from bs4 import BeautifulSoup


def get_course(path):
    course_id = parse.parse_qs(parse.urlsplit(path).query)["content"]
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

while True:
    for course_row in soup.find_all("div", {"class": "ClassRow"}):
        course_path = course_row["data-url"]
        course = get_course(course_path)

        if course not in courses:
            course_url = "https://lsa.umich.edu/cg/" + course_path

            print("Scraping ", course_url, "...", sep='')

            course_req = requests.get(course_url, headers)
            course_soup = BeautifulSoup(course_req.content, "html5lib")

            # os = Open Seats, ors = Open Restricted Seats, wl = Wait List
            course_dict = {"os": 0, "ors": 0, "wl": 0}

            for section in course_soup.find_all("div", {"class": "clsschedulerow"}):
                section_data = [x for x in section.div.div.stripped_strings]

                # Only add the section if it's a primary section for enrollment
                if str(section_data[3]) == "P":
                    last_value = ""

                    # section_data is in a flat list so refer to the previous element to determine the type of each value
                    for value in section_data:
                        # Add the section's data to the course's tota;
                        if value.isnumeric():
                            if last_value == "Open Seats:":
                                course_dict["os"] += int(value)
                            elif last_value == "Open Restricted Seats:":
                                course_dict["ors"] += int(value)
                            elif last_value == "Wait List:":
                                course_dict["wl"] += int(value)
                                break

                        last_value = value

            courses[course] = course_dict
            print("Retrieved data for ", course, ": ", course_dict, sep='')

    # Scrape all pages of the search results
    # If there is no next page then exit the loop
    next_a = soup.find("a", {"id": "contentMain_hlnkNextTop"})
    if next_a is None:
        break

    # Set the next page to be scraped to the next page of the search results
    next_req = requests.get("https://lsa.umich.edu/cg/" + next_a["href"], headers)
    soup = BeautifulSoup(next_req.content, "html5lib")

print("Finished scraping ", len(courses), " courses")

# Dump all course data to a json file for later use
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
with open(timestamp + ".json", "w") as fp:
    json.dump(courses, fp)