# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html


import scrapy

class RaceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    venue = scrapy.Field()
    raceurl = scrapy.Field()
    racedate= scrapy.Field()
    racename= scrapy.Field()
    racecourse= scrapy.Field()
    raceclass= scrapy.Field()
    racetime = scrapy.Field()
    racetype = scrapy.Field()
    raceclass = scrapy.Field()
    distance= scrapy.Field()
    going= scrapy.Field()

class RunItem(scrapy.Item):
    totalwins= scrapy.Field()
    totalruns= scrapy.Field()
    isMaiden = scrapy.Field()
    trainername = scrapy.Field()
    jockeyname = scrapy.Field()
    ownername= scrapy.Field()
    diomed = scrapy.Field()
    LTOItem = scrapy.Field()

##for results
class LTOItem(scrapy.Item):
    venue = scrapy.Field()
    raceurl = scrapy.Field()
    distance= scrapy.Field()
    going= scrapy.Field()
    racecomment= scrapy.Field()

class VenueItem(scrapy.Item):
    racecourse= scrapy.Field()
    racecoursedir= scrapy.Field()
    racecourseshape= scrapy.Field()
    racecoursefeature= scrapy.Field()
    racecoursespeed= scrapy.Field()


class HorseItem(scrapy.Item):
    horsename= scrapy.Field()
    breeder = scrapy.Field()
    allowners = scrapy.Field()
    alltrainers = scrapy.Field()
