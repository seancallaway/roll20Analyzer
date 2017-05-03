import os
import re
import requests
from datetime import datetime, timedelta
import time

import sys
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException


def getScrapParse():


    path = os.path.join(sys.path[0], "config")

    f = open(path)
    EMAIL = ''
    PASSWORD = ''
    for line in f:
        if "Email:" in line:
            EMAIL = line.split("Email:")[1].strip()
        if "Password:" in line:
            PASSWORD = line.split("Password:")[1].strip()

    f.close()

    URL = 'https://app.roll20.net/sessions/new'
    jarUrl = 'https://app.roll20.net/campaigns/chatarchive/1610304'#todo take this out of hard code


    chromeDriver = os.path.join(sys.path[0], "chromedriver.exe")
    browser = webdriver.Chrome(chromeDriver)
    browser.set_window_size(20, 20)
    browser.set_window_position(50, 50)
    browser.get(URL)

    usernameElements = browser.find_elements_by_name("email")
    passwordElements = browser.find_elements_by_name("password")

    for e in usernameElements:
        try:
            e.send_keys(EMAIL)
        except ElementNotVisibleException:
            print()

    for e in passwordElements:
        try:
            e.send_keys(PASSWORD)
        except ElementNotVisibleException:
            print()

    browser.find_element_by_class_name("calltoaction").click()
    browser.get(jarUrl)
    time.sleep(10)

    html = browser.page_source
    browser.close()

    soup = BeautifulSoup(html, 'html.parser')  # make soup that is parse-able by bs

    generalmatch = re.compile('message \w+')
    chatContent = soup.findAll("div", {"class": generalmatch})
    return chatContent


def getParse(path):
    f = open(path)
    soup = BeautifulSoup(f.read(), 'html.parser')  # make soup that is parse-able by bs
    f.close()
    generalmatch = re.compile('message \w+')

    chatContent = soup.findAll("div", {"class": generalmatch})

    return chatContent

'''
gets a path to a file and a hour number returns a subset of the parsed data
that inclueds data between the first message how many hours befor the first message

This is a bad solution to roll 20 not showing a date for time stamps
'''
def getParseRollbackHours(path, hoursBack):
    chatContent = getParse(path)
    hoursBack = hoursBack * 3600
    first = True
    firstTime = ""

    for index, chat in enumerate(reversed(chatContent)):
        for ch in chat.contents:
            if not isinstance(ch, NavigableString):
                s = ch.attrs.get("class")
                if not isinstance(s, type(None)):
                    if any("tstamp" in f for f in s):
                        timeSplit = ch.string.split()
                        time = timeSplit.pop()
                        chTime = datetime.strptime(time, '%I:%M%p')

                        if first:
                            firstTime = chTime
                            first = False
                        elif chTime < firstTime - timedelta(seconds = hoursBack):
                            return chatContent[len(chatContent) - index:]
    return chatContent

'''
Gets a path to a file and 2 date strings to return a subset of the parsed data

This code is was broken since march 18 2017 roll20 now only shows the time in the roll not the full date
'''
def getParseTimeRange(path, date1String, date2String):
    chatContent = getParse(path)
    date1 = datetime.strptime(date1String, '%b %d %Y')
    date2 = datetime.strptime(date2String, '%b %d %Y')

    startMessageIndex = 0
    startFound = False
    endMessageIndex = len(chatContent)
    lastDateFound = ""

    if date2.date() < date1.date():
        return chatContent[startMessageIndex : endMessageIndex]

    for index, chat in enumerate(chatContent):
        for ch in chat.contents:
            if not isinstance(ch, NavigableString):
                s = ch.attrs.get("class")
                if not isinstance(s, type(None)):
                    if any("tstamp" in f for f in s):
                        try:
                            chDate = datetime.strptime(ch.string, '%B %d, %Y %I:%M%p')
                            lastDateFound = chDate
                        except ValueError:
                            chDate = lastDateFound

                        if chDate.date() >= date1.date() and not startFound:
                            startMessageIndex = index
                            startFound = True
                        if date2.date() < chDate.date():
                            endMessageIndex = index - 1
                            return chatContent[startMessageIndex : endMessageIndex]

    return chatContent[startMessageIndex : endMessageIndex]