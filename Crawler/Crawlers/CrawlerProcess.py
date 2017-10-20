from Crawler.Helpers.LinksDB import LinksDB
from Crawler.Helpers.JSONDB import JSONDB
from Crawler.Objects.ObjectLink import ObjectLink
from Crawler.SmartCrawlers.CrawlerBasic import CrawlerBasic
from Server.ServerAPI import ServerAPI


class CrawlerProcess(CrawlerBasic):

    cssBreadcrumbsChildrenList = ''
    cssBreadcrumbsChildrenListElementHref = ''
    cssBreadcrumbsChildrenListElement = ''

    cssTitle = ""
    cssAuthor = ""
    cssAuthorLink = ""
    cssFullDescription = ""

    cssDateText = ""
    cssDate = ""

    cssParent = ''

    #variables

    author = ''
    authorLink = ''
    authorAvatar = ''

    parents = []
    parentId = ''

    removeShortDescription = False

    saveJSONFile = False

    # Process Data and Create new Objects
    def processScrapedData(self, url):

        self.title = self.cleanText(self.title)
        self.fullDescription = self.cleanText(self.fullDescription)
        self.shortDescription = self.cleanText(self.shortDescription)
        self.author = self.cleanText(self.author)

        self.parentId = self.createParents()

        if self.saveJSONFile and self.validate() != '':
            JSONDB.addJSONObject(self.domain, self.toJSON())

        return None

    def crawlerProcess(self, response, url):

        super().crawlerProcess(response, url)

        self.parents = []

        if self.removeShortDescription:
            self.shortDescription = ''
            self.ogDescription = ''

        if self.cssAuthor != '':
            self.author = self.extractFirstElement(response.css(self.cssAuthor))

        if self.cssAuthorLink != '':
            self.authorLink = self.extractFirstElement(response.css(self.cssAuthorLink))

        self.fullDescription = ''.join(response.css(self.cssFullDescription).extract()).strip()

        if self.cssTitle != '':
            self.title = self.extractFirstElement(response.css(self.cssTitle))

        if len(self.cssParent) > 0:

            self.parents = []

            parent = response.css(self.cssParent)
            parentText = self.extractFirstElement(parent.css('::text'))
            parentURL = ' '.join((parent.css('::attr(href)').extract()))

            if parentText != '' and parentURL != '':
                self.parents.append({'name': parentText, 'url': parentURL, 'index': 1})

        if self.cssDateText != '':  # text format like 22 Jul 2017
            date = ' '.join(response.css(self.cssDate).extract()).strip()
            print("DATEEE", date)
            self.date = dateparser.parse(date)
        else:  # timestamp format
            if self.cssDate != '':
                if self.extractFirstElement(response.css(self.cssDate)) == '':
                    self.fullDescription = ''
                else:
                    self.date = self.extractFirstElement(response.css(self.cssDate))

        if len(self.title) > 0 and len(self.cssBreadcrumbsChildrenList) > 0:

            self.parents = []
            for i in reversed(range(1, 100)):
                parent = response.css(self.cssBreadcrumbsChildrenList+':nth-child('+str(i)+')')
                parentText = self.extractFirstElement(parent.css(self.cssBreadcrumbsChildrenListElement+'::text'))
                parentURL = self.extractFirstElement(parent.css(self.cssBreadcrumbsChildrenListElementHref+'::attr(href)'))

                if parentText != '':
                    self.parents.append({'name':parentText, 'url': parentURL, 'index': i})


            self.parents = list(reversed(self.parents)) #changing the order

    # ---------------------
    # ---------------------
    # ---------------------- GRAND PARENTS
    # ---------------------
    # ---------------------
    def createParents(self):

        grandparentId = self.forumGrandParentId

        # if len(self.parents) == 0:
        #     self.parents.append({'name': '', 'url': self.url})

        if len(self.parents) > 0:
            ok = False
            for parent in self.parents:
                if parent['name'] == '':
                    ok = True

            if ok == False:
                self.parents = [{'name': '', 'url': self.url}] + self.parents

        for parent in self.parents:

            parentName = self.websiteName+' '+parent['name']
            parentObject = LinksDB.findLinkObjectAlready(self.domain, parent['url'], title=parentName, description='')

            print("@@@@@@@@@@@@@", parentObject)

            if parentObject is None:

                image = self.websiteImage or self.ogImage
                if (image == '') and (len(self.images) > 0): image = self.images[0]

                forumId = ServerAPI.postAddForum(self.url, self.user, grandparentId, self.websiteName +" "+ parent['name'],
                                                 self.websiteName + " " + parent['name'], self.websiteName +" "+ parent['name'],
                                                 image,
                                                 self.websiteCover,
                                                 self.keywords,
                                                 self.date, self.websiteCountry or self.language, self.websiteCity, self.websiteLanguage or self.language, -666, -666)

                parentObject = ObjectLink(parent['url'], 'forum', forumId, parentName, grandparentId)
                LinksDB.addLinkObject(self.domain, parentObject)

            if parentObject is not None:
                grandparentId = parentObject.id
                #print("grandparentId   ",grandparentId)

        return grandparentId

    def toString(self):

        super().toString()

        if len(self.parents) > 0: print("parents", self.parents)

        if isinstance(self.author, str):
            if self.author != '': print("author:", self.author, self.authorLink)
            if self.authorAvatar != '': print("authorAvatar", self.authorAvatar)
        else:
            print("Author")
            self.author.toString()

    def toJSON(self):

        json = super().toJSON()

        if isinstance(self.author, str):
            if self.author != '' :  json["author"] =  self.author
            if self.authorLink != '':  json["authorLink"] =  self.authorLink
            if self.authorAvatar != '':  json["authorAvatar"] =  self.authorAvatar
        else:
            json.author = self.author.toJSON()

        return json