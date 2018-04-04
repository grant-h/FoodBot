#!/usr/bin/env python
# coding: utf-8
# A simple Food focused Slack bot in python
#
# Grant Hernandez <grant.h.hernandez@gmail.com>

from IPython import embed
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

FOOD_URL = "https://www.bsd.ufl.edu/dining/Menus/ArMenu.aspx"

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

        data = soup.table("td", {"class" : ["dateclass", "menuitems"]})
        data_table = []
        row_data = []
        col = 0

        for d in data:
            if "dateclass" in d['class']:

                row_data += [d.text.strip()]
            elif "menuitems" in d['class']:
                foods = []
                for food in d("tr"):
                    foods += [food.font.text.strip()]

                row_data += [foods]
                new_row = True

            col += 1

            if col == 6:
                data_table += [row_data]
                row_data = []
                col = 0

        return self.process_data(data_table)

    def split_weeks(self, table):
        dow = [u"Monday", u"Tuesday", u"Wednesday", u"Thursday", u"Friday"]
        week = []

        start = -1
        rowi = 0

        def rec_find(obj, item):
            if isinstance(obj, list):
                for x in obj:
                    if isinstance(x, list):
                        if rec_find(x, item):
                            return True
                    else:
                        if x.find(item) != -1:
                            return True

                return False
            else:
                return obj.find(item) != -1

        # Column header finding heuristic
        while rowi < len(table):
            row = table[rowi]

            if start == -1:
                found = 0

                # for each column, search for the day of the week
                for col in row:
                    for d in dow:
                        if rec_find(col, d):
                            found += 1
                            break

                if found > 2:
                    start = rowi
            else:
                found = 0

                # for each column, search for the day of the week
                for col in row:
                    for d in dow:
                        if rec_find(col, d):
                            found += 1
                            break

                if found > 2:
                    week += [table[start:rowi]]
                    start = rowi

            rowi += 1

        if start != -1:
            week += [table[start:]]

        return week

    def process_data(self, table):
        weeks = self.split_weeks(table)

        if len(weeks) < 1:
            raise ValueError("No valid weeks found after parsing")

        for week in weeks:
            if self.process_week(week):
                return

        print pprint.pprint(weeks)
        raise ValueError("Found at least one valid week, but never found a matching day")

    def process_week(self, week):
        today = datetime.today()

        times = week[0]
        col = -1

        for i, t in enumerate(times):
            t = t.encode('ascii', 'ignore')

            if t is '':
                continue

            ref = datetime.strptime(t, '%A,%B%d')

            if ref.month == today.month and ref.day == today.day:
                col = i
                break

        if col == -1:
            return False

        foods = []
        for i in week[1:]:
            for this_col,j in enumerate(i):
                if this_col == col:
                    foods += [j]

        food_types = []
        for i in week[1:]:
            for this_col,j in enumerate(i):
                if this_col == 0:
                    food_types += [j]

        color = COLORS[(today.month + today.day + today.year) % len(COLORS)]

        return self.output_data(color, food_types, foods)

    def output_data(self, color, food_types, data):
        text = u""
        closed = False

        for typeIdx, cat in enumerate(data):
            out = u"*"+food_types[typeIdx] + "*\n"

            for bullet in cat:
                if 'closed' in bullet.lower():
                    closed = True
                    break

                words = bullet.encode('ascii', 'ignore').lower().split(" ")
                icons = []

                for w in words:
                    if w in EMOJI_DICT:
                        emoji = EMOJI_DICT[w]

                        if emoji not in icons:
                            icons += [emoji]

                out += u"• " + bullet + " " + "".join(icons) + "\n"

            text += out + "\n"

        header = ""
        if closed:
            body = u"The café is closed today :slightly_frowning_face:"
        else:
            body = text

        today_note = "Today, {}".format(datetime.today().strftime("%A, %B %d"))

        extra = {"title" : "Arredondo Café - {}".format(today_note), "title_link" : FOOD_URL}

        if self.mock:
            print extra
            print header
            print body
            return True

        # make the post to all servers!
        for i in self.slack:
            i.postRich(header, body, color, "", extra)

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
