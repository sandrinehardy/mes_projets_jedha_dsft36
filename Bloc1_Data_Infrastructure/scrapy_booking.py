
import os
import logging
import scrapy
from scrapy.crawler import CrawlerProcess

class BookingListeSpider(scrapy.Spider):
    name = "booking_liste"

    start_urls = ["https://www.booking.com/searchresults.fr.html?ss=Colmar&checkin=2026-10-17&checkout=2026-10-18&group_adults=2&no_rooms=1&group_children=0"]

    def parse(self, response):
        print("Status code :", response.status, "| taille de la page :", len(response.body), "octets", "\n")
        with open('page_verification.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        hotels = response.css("div[data-testid='property-card']")
        if len(hotels) == 0:
            print("Aucun hotel trouve : Booking.com renvoie une page de verification anti-robot \n")
        for hotel in hotels:
            yield {
                "nom": hotel.css("div[data-testid='title']::text").get(),
                "url": hotel.css("a[data-testid='title-link']::attr(href)").get(),
                "note": hotel.css("div[data-testid='review-score'] > div:nth-child(2)::text").get()
            }

filename = "hotels_liste.json"

# Si le fichier existe déjà, on le supprime
if filename in os.listdir('.'):
    os.remove(filename)

process = CrawlerProcess(settings = {
    'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    'LOG_LEVEL': logging.WARNING,
    'DOWNLOAD_DELAY': 2,
    "FEEDS": {
        filename : {"format": "json"},
    }
})

process.crawl(BookingListeSpider)
process.start()
