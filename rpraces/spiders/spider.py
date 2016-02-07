import scrapy
from datetime import datetime
from rpraces import items
from rpraces.utilities import *
import urlparse
import unicodedata

dir_pat = re.compile("^.*(left|right)-handed.*")
rcspeed_pat = re.compile("^.*(galloping|stiff|tight).*")
rcfeature_pat = re.compile("^.*(undulating|uphill|flat).*")
rcshape_pat = re.compile("^.*(circle|horseshoe|oval|pear|triangle).*")
dgr_pat = re.compile(r'^([0-9.]{1,4})(\w+)')
gearl1_pat = re.compile("(\D*)\d{1,4}/\d{1,2}")
spl1_pat = re.compile("\D*(\d{1,4}/\d{1,2})")
raceidpat = re.compile(r'.*race_id=(\d+).*')
class HorseSpider(scrapy.Spider):

    name = 'rpraces'
    handle_httpstatus_list = [404,301]
    #301 means moved to results

    def __init__(self, date, *args, **kwargs):
        super(HorseSpider, self).__init__(*args, **kwargs)
        self.date = datetime.strptime(date, '%Y-%m-%d') #2016-02-06
        self.domain = 'www.racingpost.com'
        self.nomeets = 0
        self.venues = []
        self.start_urls = [
            'http://{domain}/horses2/cards/home.sd?r_date={date}'.format(
                domain=self.domain, date=date)
        ]
    ##if 301?
    def parse(self, response):
        cards_path = '//div[./table[@class="cardsGrid"]][.//h3[text()!='\
            '"WORLDWIDE STAKES RACES"]]//a[@title="Click to view card: '\
            'View Card"]/@href'
        self.nomeets = float(response.xpath("count(//div[@class='crBlock'])").extract()[0])
        self.venues = response.xpath("//table[@class='raceHead']/tbody/tr/td[@class='meeting']/h3/a/text()")
        for url in response.xpath(cards_path).extract():
            yield scrapy.Request(
                'http://{domain}{url}'.format(domain=self.domain, url=url),
                callback=self.parse_card)
    '''
    racenumber, racecourse, racedate, racetime, raceclass, racetype
    '''
    def parse_card(self, response):
        race_url = response.url[0]
        raceid = re.match(raceidpat, response.url).group(1)
        # print race_id
        racename_part_1 = response.xpath(
            '//div[@class="pageHeader cardHeader"]//div[@class="info"]/p'
            '//strong[@class="uppercase"]/text()').extract()
        racename_part_2 = response.xpath(
            '//div[@class="pageHeader cardHeader"]//div[@class="info"]/p'
            '/strong/text()').extract()
        racename_part_3 = response.xpath(
            '//div[@class="pageHeader cardHeader"]//div[@class="info"]/p'
            '/text()[2]').extract()
        format_text = lambda text: text[0].strip().encode('UTF-8') if text else ''
        racename = '{} {} {}'.format(
            format_text(racename_part_1),
            format_text(racename_part_2),
            format_text(racename_part_3)
        ).decode('UTF-8')

        racetype = getracetype(racename)
        raceclass = getraceclass(racename)
        imperialdistance = " ".join(response.xpath("//li[text()[contains(.,'Distance:')]]/strong/text()").extract())
        racedistance = imperialtofurlongs(imperialdistance)

        norunners = response.xpath("//li[text()[contains(.,'Runners:')]]/strong/text()").extract()[0].strip()

        racegoing_ = response.xpath("//li[text()[contains(.,'Going:')]]/strong/text()").extract()[0].strip()
        racegoing = getgoingcode(racegoing_)
        racecoursename = " ".join( response.xpath("//h1[contains(@class,'cardHeadline')]//span[@class='placeRace']/text()").extract()).strip()

        racecoursecode = rcnametocode(racecoursename)
        # racetime = response.xpath("//h1[contains(@class,'cardHeadline')]//span[not(@class)]/text()").extract()[0]
        racetime = response.xpath("//span[@class='navRace']/span/text()").extract()[0]
        xp1 = "count(//table[@class='raceHead']/tbody/tr/td[@class='meeting']/h3/a[contains(text(), '%s')]/../../../../../../table[@class='cardsGrid']//tr)" % racecoursename.upper()
        xp2 = "//table[@class='raceHead']/tbody/tr/td[@class='meeting']/h3/a[contains(text(), '%s')]/../../../../../../table[@class='cardsGrid']//tr/th[@class='rTime']//a/text()" % racecoursename.upper()
        xp1 = unicodedata.normalize('NFKD', xp1).encode('ascii','ignore')
        noraces = response.xpath(xp1).extract()[0]
        alltimes = response.xpath(str(xp2)).extract()
        print(xp1, xp2)

        print ("rc, noraces:%s - %s - %s" % (racecoursename, racecoursecode, noraces))
        print alltimes
        #racenumber
        # diomed_verdict
        # print("diomed", diomed)

        ##horses
        # horse_path = '//table[@id="sc_horseCard"]//'\
        #             'a[@title="Full details about this HORSE"]/@href'
        # for url in response.xpath(horse_path).extract():
        #     request = scrapy.Request(url, callback=self.parse_horse)
        #     request.meta['racename'] = racename
        #     request.meta['raceclass'] = raceclass
        #     request.meta['racetype'] = racetype
        #     request.meta['racetime'] = racetime
        #     request.meta['racecourse'] = racecourse

        for h in response.xpath('//table[@id="sc_horseCard"]//tr[@class="cr"]'):
            horseurl= h.xpath("td[3]/a[contains(@title,'HORSE')]/@href").extract()[0] #Horsid
            request = scrapy.Request(horseurl, callback=self.parse_horse)
            request.meta['horsenumber'] = int(h.xpath("td[1]/strong/text()").extract()[0]) #horsenumber
            request.meta['currentownerurl'] = h.xpath("td[2]/a[contains(@title,'OWNER')]/@href").extract()[0]
            request.meta['gear'] = " ".join(h.xpath("td[3]/span/text()").extract()).strip()
            request.meta['age'] = int(h.xpath("td[4]/text()").extract()[0])
            # print re.match(r'.*owner_id=(\d+).*',ownerurl).group(1) #currentownerid
            request.meta['horseurl'] = horseurl
            _diomed = h.xpath("../tr/td[@class='cardItemInfo']/p[@class='diomed']/text()").extract()[0]
            request.meta['horsename']= h.xpath("td[3]/a[contains(@title,'HORSE')]/b/text()").extract()[0] #horsename
            if h.xpath("td[6]/div[1]/a[contains(@title,'JOCKEY')]/text()").extract():
                request.meta['jockeyname']=  h.xpath("td[6]/div[1]/a[contains(@title,'JOCKEY')]/text()").extract()[0]  #janme
            else:
                request.meta['jockeyname'] = None
            request.meta['trainername']=  h.xpath("td[6]/div[2]/a[contains(@title,'TRAINER')]/text()").extract()[0]  #Tanme
            # print h.xpath("td[9]/button/div/div/text()").extract()  #janme odds?
            # print h.xpath("button[contains(@title,'bet')]//@title").extract()
            request.meta['racename'] = racename
            request.meta['norunners'] = norunners
            request.meta['racegoing'] = racegoing
            request.meta['raceclass'] = raceclass
            request.meta['racedistance'] = racedistance
            request.meta['racetype'] = racetype
            request.meta['raceurl'] = race_url
            request.meta['raceid'] = raceid
            request.meta['racetime'] = racetime
            request.meta['racecoursename'] = racecoursename
            request.meta['racecoursecode']= racecoursecode
            request.meta['diomed'] = _diomed
            #raceid for subs call to betting





            yield request

    # horsenumber isMaiden L1stats
    def parse_horse(self, response):

        horsename = mynormalize(response.xpath('//div[@id="otherHorses"]//option'
            '[@selected]/text()').extract()[0])
        trainername = response.xpath("//ul[@id='detailedInfo']/li[contains(text(), 'Trainer')]/div/a/text()").extract()[0]
        format_text = lambda text: text[0].strip().encode('UTF-8') if text else ''
        owners_ = ";".join( response.xpath("//ul[@id='detailedInfo']/li[contains(text(), 'Owner')]/b//text()").extract())
        owners = tf(owners_.strip().split(";"))
        # owners = format_text(owners).decode('UTF-8')
        breeder = response.xpath("//ul[@id='detailedInfo']/li[contains(text(), 'Breeder')]/b/text()").extract()[0]

        totalruns_ = response.xpath("//table[@class='grid right']//td[2]/text()").extract()
        totalwins_ = response.xpath("//table[@class='grid right']//td[3]/text()").extract()
        totalwins = sum( [int(x) for x in totalwins_])
        totalruns = sum( [int(x) for x in totalruns_])
        # print("owners:%s " % owners)
        # print("trainername:%s " % trainername)
        # print("totalwins/runs: {0}-{1}").format(totalwins, totalruns)
        #racedate, racecourse, distgoing, raceconds, l1pos


        ##STATS
        ## LTO get raceid push all raceids to CSV to crawl with url_raceresults crawler
        ##
        ##Any previous runs?
        LTO = {}
        noformfound = response.xpath("//div[@id='horse_form']/div[@class='nodataBlock']/*/text()").extract()
        if not noformfound:
            for tr in response.xpath("//div[@id='horse_form']/table[@class='grid']//tr[2]"):

                l1racedate_ = tr.xpath("td[1]/a/text()").extract()[0]
                #convert format 31Oct15
                LTO['l1racedate'] = datetime.strptime(l1racedate_, "%d%b%y")
                LTO['dayssincelastrun'] = (self.date- LTO['l1racedate']).days
                LTO['l1racecourse'] = tr.xpath("td[2]/b/a/text()").extract()[0]
                thisdir = tr.xpath("td[3]/b[@class='black']/a/@title").extract()
                if thisdir:
                    if re.match(dir_pat, thisdir[0]):
                        LTO['l1racecoursedir'] = re.match(dir_pat, thisdir[0]).group(1)
                    if re.match(rcspeed_pat, thisdir[0]):
                        LTO['l1racecoursespeed'] = re.match(rcspeed_pat, thisdir[0]).group(1)
                    if re.match(rcfeature_pat, thisdir[0]):
                        LTO['l1racecoursefeature'] = re.match(rcfeature_pat, thisdir[0]).group(1)
                    if re.match(rcshape_pat, thisdir[0]):
                        LTO['l1racecourseshape'] = re.match(rcshape_pat, thisdir[0]).group(1)

                l1distancegoing= " ".join(tr.xpath("td[2]/b/text()").extract()).strip()
                ##parse race result
                l1raceurl_ = tr.xpath("td[1]/a/@href").extract()[0]
                LTO['l1raceurl'] = urlparse.urljoin("http://www.racingpost.com", l1raceurl_)

                LTO['l1distance'] = re.match(dgr_pat, l1distancegoing).group(1)
                LTO['l1going'] = re.match(dgr_pat, l1distancegoing).group(2)
                l1racecoursetype = tr.xpath("td[2]/b/a/@title/text()").extract()
                l1raceconditions=  " ".join(tr.xpath("td[2]/text()").extract()).strip()
                if l1raceconditions:
                    LTO['l1racetype'] = getracetypeLn(l1raceconditions)
                    LTO['l1raceclass'] = getraceclassLn(l1raceconditions)
                else:
                    LTO['l1racetype']= None
                    LTO['l1raceclass'] = None
                LTO['l1racecomment']= tr.xpath("td[4]/a/@title").extract()[0]
                LTO['l1pos']= tr.xpath("td[4]/b/text()").extract()[0]
                l1spgear = " ".join(tr.xpath("td[4]/a/following-sibling::text()").extract()).strip()
                if re.match(spl1_pat, l1spgear):
                    spl1_ = re.match(spl1_pat, l1spgear).group(1)
                    LTO['l1sp'] = decimalizeodds(spl1_)
                if re.match(spl1_pat, l1spgear):
                    LTO['l1gear'] = re.match(gearl1_pat, l1spgear).group(1).strip()
                LTO['l1jockey']= format_text(tr.xpath("td[5]/a/text()").extract())


                ########
                # print("------------l1racedate, racecourse, dist, going, racetype, raceclass, l1pos")
                # print(l1racedate, l1racecourse, l1distance, l1going, getracetypeLn(l1raceonditions), getraceclassLn(raceconditions), l1pos)
                # print("---racecomment, l1sp, l1j")
                # print(l1racecomment, l1sp, l1jockey)
                # print("Venue Stats L1----------------------")
                # print(l1racecourse, l1racecoursedir,l1racecourseshape,l1racecoursefeature,l1racecoursespeed)
        else:
            pass
        # wgts_path = '//div[@id="horse_form"]//table//tr[@id][@class="fl_F"]/td[4]/text()'
        # wgts = [wgt.strip() for wgt in response.xpath(wgts_path).extract()[:5]]


        horsename_query = horsename.encode('UTF-8').replace(' ', '+')
        horsename_url = 'http://www.pedigreequery.com/{}'.format(
            horsename_query)
        request = scrapy.Request(
            horsename_url,
            callback=self.return_object,
        )
        raceid = response.meta['raceid']
        racedatestr = datetime.strftime(self.date, '%Y-%m-%d')
        betting_url = 'http://betting.racingpost.com/horses/cards/card.sd?race_id={0}&r_date={1}#racingCard=standard&infoTabs=diomed_verdict'.format(raceid, racedatestr)
        # request = scrapy.Request(
        #             betting_url,
        #             callback=self.parse_bettingrace,
        #         )

        request.meta['racedate'] = self.date
        request.meta['racename'] = response.meta['racename']
        request.meta['betting_url'] = betting_url
        # request.meta['bestodds'] = response.meta['bestodds']
        request.meta['raceclass'] = response.meta['raceclass']
        request.meta['racedistance'] = response.meta['racedistance']
        request.meta['racegoing'] = response.meta['racegoing']
        request.meta['norunners'] = response.meta['norunners']
        request.meta['racetype'] = response.meta['racetype']
        request.meta['raceurl'] = response.meta['raceurl']
        request.meta['raceid'] = response.meta['raceid']
        request.meta['racetime'] = response.meta['racetime']
        request.meta['racecoursename'] = response.meta['racecoursename']
        request.meta['horsenumber'] = response.meta['horsenumber']
        request.meta['horsename'] = response.meta['horsename']
        request.meta['trainername'] = response.meta['trainername']
        request.meta['horseurl'] = response.meta['horseurl']
        request.meta['breeder'] = breeder
        request.meta['owners'] = owners
        request.meta['currentownerurl'] = response.meta['currentownerurl']
        request.meta['age'] = response.meta['age']
        request.meta['gear'] = response.meta['gear']
        request.meta['diomed'] = response.meta['diomed']
        request.meta['jockeyname'] = response.meta['jockeyname']
        request.meta['totalwins'] = totalwins
        request.meta['isMaiden'] = totalwins==0
        request.meta['totalruns'] = totalruns
        if LTO:
            request.meta['l1racedate'] = LTO['l1racedate']
            request.meta['l1raceurl'] = LTO['l1raceurl']
            request.meta['dayssincelastrun'] = LTO['dayssincelastrun']
            request.meta['l1racecourse'] = LTO['l1racecourse']
            request.meta['l1distance'] = LTO['l1distance']
            request.meta['l1going'] = LTO['l1going']

            request.meta['l1pos'] = LTO['l1pos']
            request.meta['l1racecomment'] = LTO['l1racecomment']
            request.meta['l1sp'] = LTO['l1sp']
            request.meta['l1jockey'] = LTO['l1jockey']
            request.meta['l1racetype'] = LTO['l1racetype']
            request.meta['l1raceclass'] = LTO['l1raceclass']
        # request.meta['wgts'] = wgts
        return request.meta
        # yield request

    ## go to betting.racingpost.com NEED RACEID
    ## get SPPOs and currentime oddsbarfavorite

    #replace with betting page
    def parse_bettingrace(self, response):
        print response.url
        '''
        get oddsrank
        updatetime
        notips

        done call return object to sort into nested items
        return as JSON
        import into MONGODB
        also return CSV with l1raceids
        '''

    def return_object(self, response):
        _wins = response.meta.get('totalwins')
        hi = items.HorseItem(
            horsename=response.meta.get('horsename'),
            )

        rai = items.RaceItem(
            racedate=self.date,
            racecourse=response.meta.get('racecourse'),
            raceclass=response.meta.get('raceclass'),
            racetype=response.meta.get('racetype'),
            racetime=response.meta.get('racetime'),
            racename=response.meta.get('racename'),
            )
        items.RunItem(
            horsenumber=response.meta.get('horsenumber'),
            totalwins= response.meta.get('totalwins'),
            totalruns= response.meta.get('totalruns'),
            isMaiden = _totalwins ==0,
            trainername = response.meta.get('trainername'),
            jockeyname = response.meta.get('jockeyname'),
            currentowner= response.meta.get('currentowner'),
            l1racecourse= response.meta.get('l1racecourse'),
            l1racedate = response.meta.get('l1racedate'),
            l1racecomment= response.meta.get('l1racecomment'),
            l1distancegoing= response.meta.get('l1distancegoing'),
            l1raceonditions= response.meta.get('l1raceonditions'),
            l1sp= response.meta.get('l1sp'),
            l1jockey= response.meta.get('l1jockey'),
            l1trainer = response.meta.get('l1trainer'),
            horsestats= response.meta.get('horsestats'),
            horse = dict(hi),
            race = dict(rai),
            )

        yield items.RunItem.itemloader()


    #pedigree query!
    # def parse_horse_stat(self, response):
    #     horsestats_path = 'normalize-space(//table//center/table[1]//center)'
    #     horsestats = response.xpath(horsestats_path).extract()[0]
    #
    #     items.HorseItem(
    #         horsename=response.meta.get('horsename'),
    #     )
    #
    #     items.RunItem(
    # totalwins= response.meta.get('totalwins')
    # totalruns= response.meta.get('totalruns')
    # isMaiden = _totalwins ==0,
    # trainername = response.meta.get('trainername')
    # jockeyname = response.meta.get('jockeyname')
    # currentowner= response.meta.get('currentowner')
    # l1racecourse= response.meta.get('l1racecourse')
    # l1racedate = response.meta.get('l1racedate')
    # l1racecomment= response.meta.get('l1racecomment')
    # l1distancegoing= response.meta.get('l1distancegoing')
    # l1raceonditions= response.meta.get('l1raceonditions')
    # l1sp= response.meta.get('l1sp')
    # l1jockey= response.meta.get('l1jockey')
    # l1trainer = response.meta.get('l1trainer')
    # horsestats= response.meta.get('horsestats')
    #
    #     )
    #     items.RaceItem(
    #         racedate=self.date,
    #         racecourse=response.meta.get('racecourse'),
    #         raceclass=response.meta.get('raceclass'),
    #         racetype=response.meta.get('racetype'),
    #         racetime=response.meta.get('racetime'),
    #         racename=response.meta.get('racename'),
    #
    #     )
    #     yield items.RpracesItem(
    #
    #         bestodds=response.meta.get('bestodds'),
    #
    #         # wgts=response.meta.get('wgts'),
    #         horsestats=horsestats,
    #     )
