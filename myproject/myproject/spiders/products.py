import scrapy
import json
import re


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["junaidjamshed.com"]
    start_urls = ["https://www.junaidjamshed.com/women-collections"]

    def parse(self, response):
        category_link = response.css("a.level-top::attr(href)").getall()
        for link in category_link:
            full_link = response.urljoin(link)
            yield scrapy.Request(
                url=full_link,
                callback=self.parse_category,
            )

    def parse_category(self, response):
        product_link = response.css("a.product-item-link::attr(href)").getall()
        for link in product_link:
            full_link = response.urljoin(link)
            yield scrapy.Request(
                url=full_link,
                callback=self.parse_product,
            )
        next_page = response.css("a.action.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_category,
            )

    def parse_product(self, response):
        stock_info = response.css("div.product-info-stock-sku")

        raw_json = response.xpath('//script[contains(text(), "jsonSwatchConfig")]/text()').get()
        sizes = []
        if raw_json:
            match = re.search(r'"jsonSwatchConfig":(\{.*?\})\s*,\s*"mediaCallback"', raw_json, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    for key, value in data.items():
                        for item in value.values():
                            if isinstance(item, dict) and "value" in item:
                                sizes.append(item["value"])
                except Exception as e:
                    self.logger.error(f"Size extract error: {e}")

        yield {
            "Title": response.css("span.base::text").get(),
            "Price": response.css("span.price::text").get(),
            "SKU#": stock_info.css("div.product.attribute.sku div.value::text").get(),
            "Article-Code": stock_info.css("div.product.attribute.sku.article-code span::text").get(),
            "Availability": stock_info.css("div.stock.available span::text").get(),
            "Sizes": sizes,
            "URL": response.url
        }
