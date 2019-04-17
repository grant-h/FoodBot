#!/usr/bin/env python
# coding: utf-8
# A simple Food focused Slack bot in python
#
# Grant Hernandez <grant.h.hernandez@gmail.com>

try:
    from IPython import embed
except ImportError:
    pass

from bs4 import BeautifulSoup
from server import SlackServer, SlackPost
from datetime import datetime
from food import EMOJI_DICT

import re
import json
import urllib2
import pprint
import argparse

# From http://tools.medialab.sciences-po.fr/iwanthue/index.php
# Sorted by their color difference
COLORS = ["#6a0032", "#01cf49", "#604bf7", "#74c200", "#8900b2",
          "#b3dc3d", "#00179a", "#e2cf4a", "#ff53f4", "#008c43",
          "#e6008a", "#5d8200", "#4b7cff", "#936d00", "#0264ce",
          "#ac1c00", "#0192f7", "#ff5259", "#00aeb1", "#c30038",
          "#019abe", "#940034", "#94d7f4", "#7f3400", "#ed97ff",
          "#232e00", "#c1b9ff", "#00664b", "#ff7d8e", "#002172",
          "#c1d693", "#5a005b", "#bdd2cc", "#2a1632", "#fcbfb8",
          "#005053", "#ff99bf", "#00556d"]

FOOD_URL = "https://gatordining.campusdish.com/LocationsAndMenus/ArrendonoReitzUnion?locationId=4041&storeId=&mode=Weekly"

class FoodBotSlack():

    def __init__(self,
            slackServers,
            testing=False,
            mock=False):
        self.colormap = {}
        self.colormapIter = 0
        self.testing = testing
        self.mock = mock

        self.slack = slackServers

        if self.testing:
            print("** TESTING MODE ACTIVE")

        if self.mock:
            print("** MOCK MODE ACTIVE")
        else:
            for i in slackServers:
                print(u"- Broadcasting to {}".format(i))

    def scrape(self, url):
        response = urllib2.urlopen(url)
        html = response.read().decode('utf-8', 'ignore')

        return self.parse_html(html)

    def parse_html(self, html):
        soup = BeautifulSoup(html, "html.parser")

        days = soup.findAll("div", {"class" : ["menu__day"]})

        menu_week = []

        for d in days:
            day_name = d(class_="dayName")[0]
            day_name = day_name.text.strip()

            menu_day = {"day" : day_name, "stations": []}

            stations = d(class_="menu__station")

            for station in stations:
                station_data = {}
                st_name = station(class_="stationName")[0]
                st_name = st_name.text.strip()

                # Skip the salad bar, as it's spammy
                if "salad" in st_name.lower():
                    continue

                station_data["name"] = st_name
                station_data["items"] = []

                items = station(class_="menu__item")

                for item in items:
                    item_name = item(class_="item__name")[0]
                    item_name = item_name.text.strip()
                    station_data["items"] += [item_name]

                menu_day["stations"] += [station_data]

            menu_week += [menu_day]

        return self.process_week(menu_week)

    def process_week(self, week):
        import calendar
        today = datetime.today()

        color = COLORS[(today.month + today.day + today.year) % len(COLORS)]

        for day in week:
            if day["day"] == calendar.day_name[today.weekday()]:
                return self.output_data(day, color)

        return self.output_data(day, color, closed=True)

    def output_data(self, day, color, closed=False):
        text = u""

        for station in day["stations"]:
            out = u"*"+station["name"].capitalize() + "*\n"

            for item in station["items"]:
                item = item.capitalize()

                words = item.encode('ascii', 'ignore').lower().split(" ")

                def just_text(w):
                    m = re.match('[a-zA-Z]+', w)

                    if m:
                        return m.group(0)
                    else:
                        return None

                words = map(just_text, words)

                print words

                icons = []

                for w in words:
                    if w in EMOJI_DICT:
                        emoji = EMOJI_DICT[w]

                        if emoji not in icons:
                            icons += [emoji]

                out += u"• " + item + " " + "".join(icons) + "\n"

            text += out + "\n"

        if closed:
            body = u"The café is closed today :slightly_frowning_face:"
        else:
            body = text

        today_note = "Today, {}".format(datetime.today().strftime("%A, %B %d"))
        header = "Arredondo Café - {}".format(today_note)

        self.output_slack(header, body, FOOD_URL, color)

        return True

    def output_slack(self, header, body, link, color):
        extra = {"title" : header, "title_link" : link}

        if self.mock:
            print extra
            print body
            return True

        # make the post to all servers!
        for i in self.slack:
            i.postRich("", body, color, "", extra)

        return True

def banner():
    print("FoodBotSlack by Grant")
    print("")

def main(args):
    banner()

    slackServers = []
    configFp = None

    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--test-file")

    args = parser.parse_args()

    try:
        configName = args.config if args.config else "config.json"
        configFp = open(configName, "r")
    except IOError:
        parser.error("Invalid configuration file")

    if args.test_file:
        bot = FoodBotSlack(None, mock=True)
        return bot.parse_html(open(args.test_file, 'r').read())

    try:
        config = json.load(configFp)
    except ValueError as e:
        parser.error("JSON parsing error: " + e.message)

    configFp.close()

    print("Loaded configration file %s" % configName)

    testing = config["testing"]

    # load slack servers
    for i in config["servers"]:
        slackServers.append(
            SlackServer(
                i["url"],
                i["name"],
                i["username"],
                i["channel"],
                i["admin"],
                (i["batch_time"],
                 i["batch_amount"]),
                testing=testing,
                ))

    bot = FoodBotSlack(slackServers, testing)

    try:
        bot.scrape(FOOD_URL)
    except KeyboardInterrupt:
        print("Stopping on user Ctrl-C")

if __name__ == "__main__":
    import sys

    global EXENAME
    EXENAME = sys.argv[0]

    main(sys.argv[1:])
