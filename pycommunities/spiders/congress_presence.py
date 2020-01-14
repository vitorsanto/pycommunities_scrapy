from scrapy import Spider, Request, FormRequest
from scrapy.utils.response import open_in_browser

class CongressPresenceSpider(Spider):
    name = 'congress_presence'
    start_urls = ['https://www2.camara.leg.br/deputados/pesquisa']

    def parse(self, response):
        form = response.xpath('//form[@id="formDepAtual"]')
        congresspeople = form.xpath('.//select[@name="deputado"]/option[string(@value)]/@value').extract()
        for congressperson in congresspeople:
            #yield FormRequest(
            #    url=form.attrib['action']
            #)
            yield FormRequest.from_response(
                response=response,
                formid='formDepAtual',
                formdata={
                    'deputado': congressperson
                },
                callback=self.parse_congressperson
            )

    def parse_congressperson(self, response):
        congressperson_info = response.xpath('//ul[@class="informacoes-deputado"]/li')
        #name = congressperson_info.xpath('span[text()="Nome Civil:"]/text()')
        congressperson = {
            'name': congressperson_info.xpath('span[1]/text()').extract_first(),
            'email': congressperson_info.xpath('span[2]/text()').extract_first(),
            'phone': congressperson_info.xpath('span[3]/text()').extract_first(),
            'address': congressperson_info.xpath('span[4]/text()').extract_first(),
            'birthday': congressperson_info.xpath('span[5]/text()').extract_first(),
            'naturality': congressperson_info.xpath('span[6]/text()').extract_first(),
        }
        years = response.xpath('//li[contains(@class,"linha-tempo__item")]/a')
        for year in years:
            yield Request(
                url=year.attrib['href'],
                meta={
                    'congressperson': congressperson,
                },
                callback=self.parse_presences,
            )

        response.meta['congressperson'] = congressperson
        yield self.parse_presences(response)
    
    def parse_presences(self, response):
        congressperson = response.meta['congressperson']
        plenary_data = response.xpath('//li[@class="list-table__item"][1]')
        commission_data = response.xpath('//li[@class="list-table__item"][2]')
        current_year = response.xpath('//li[contains(@class,"linha-tempo__item")]/span/@data-ano').extract_first()

        congressperson.update({
            'year': current_year,
            'plenary': {
                'presence': plenary_data.xpath('dl/dd[1]/text()').extract_first(),
                'justified_absence': plenary_data.xpath('dl/dd[2]/text()').extract_first(),
                'unjustified_absence': plenary_data.xpath('dl/dd[3]/text()').extract_first()
            },
            'commission': {
                'presence': plenary_data.xpath('dl/dd[1]/text()').extract_first(),
                'justified_absence': plenary_data.xpath('dl/dd[2]/text()').extract_first(),
                'unjustified_absence': plenary_data.xpath('dl/dd[3]/text()').extract_first()
            }
        })
        return congressperson


