import os
import logging
import scrapy
from pathlib import Path
from scrapy.crawler import CrawlerProcess

#import pandas as pd

class BookingLocalSpider(scrapy.Spider):
    name = "booking_local"

    # df_meteo = pd.read_csv('meteo_villes.csv')
    # villes = list(df_meteo[df_meteo['top5_meteo']]['ville'])      # ex : ['La Rochelle', 'Collioure', ...]


    # Comme les pages sont enregistrées manuellement, on entre la liste manuellement
    villes = ['la_rochelle', 'collioure', 'dijon', 'strasbourg', 'colmar', 'le_havre', 'paris']

    start_urls = []
    for ville_page in villes:
        nom_page = "booking_" + ville_page.lower().replace(" ", "_") + ".html"     # La Rochelle -> booking_la_rochelle.html
        start_urls.append(Path(nom_page).resolve().as_uri())

    def parse(self, response):
        print("Page lue :", response.url.split("/")[-1])
        print("Taille de la page :", len(response.body), "octets", "\n")

        # booking_la_rochelle.html -> La Rochelle
        nom_fichier = response.url.split("/")[-1]
        ville = nom_fichier.replace("booking_", "").replace(".html", "").replace("_", " ").title()

        # Les coordonnées GPS ne sont pas dans les cartes des hôtels, mais dans des données (json)
        # écrites dans la page : "latitude":46.15,"longitude":-1.14},"pageName":"nom-de-l-hotel"
        coordonnees = {}
        blocs = response.text.split('"latitude":')
        for bloc in blocs[1:]:
            latitude = bloc.split(",")[0]
            if '"longitude":' in bloc and '"pageName":"' in bloc:
                longitude = bloc.split('"longitude":')[1].split("}")[0]
                page_name = bloc.split('"pageName":"')[1].split('"')[0]
                coordonnees[page_name] = (float(latitude), float(longitude))

        hotels = response.css("div[data-testid='property-card']")
        print("Nombre d'hôtels trouvés :", len(hotels), "\n")

        for hotel in hotels:
            # Adresse de l'hôtel sans les paramètres : .../la-fabrique-la-rochelle.fr.html
            url = hotel.css("a[data-testid='title-link']::attr(href)").get().split("?")[0]
            page_name = url.split("/")[-1].split(".")[0]

            # Note : "8,6" -> 8.6
            note = hotel.css("div[data-testid='review-score'] > div:nth-child(2)::text").get()
            if note is not None:
                note = float(note.replace(",", "."))

            # Nombre d'avis : on garde les chiffres de "2 319 expériences vécues"
            texte_avis = hotel.css("div[data-testid='review-score'] > div:nth-child(3) > div:nth-child(2)::text").get()
            nb_avis = None
            if texte_avis is not None:
                chiffres = "".join(c for c in texte_avis if c.isdigit())
                if chiffres != "":
                    nb_avis = int(chiffres)

            # Étoiles : "Note de l'établissement : 3 étoiles sur 5." -> 3
            texte_etoiles = hotel.css("button[aria-label^='Note de']::attr(aria-label)").get()
            etoiles = None
            if texte_etoiles is not None:
                etoiles = int([c for c in texte_etoiles if c.isdigit()][0])

            # Description : le texte placé juste sous la ligne de l'adresse (on recolle les morceaux de texte)
            morceaux_description = hotel.xpath(".//span[@data-testid='address-link']/ancestor::div[following-sibling::div][1]/following-sibling::div[1]//text()").getall()
            description = "".join(morceaux_description).strip()

            latitude, longitude = coordonnees.get(page_name, (None, None))

            yield {
                "ville": ville,
                "nom": hotel.css("div[data-testid='title']::text").get(),
                "url": url,
                "note": note,
                "nb_avis": nb_avis,
                "etoiles": etoiles,
                "quartier": hotel.css("span[data-testid='address-link']::text").get(),
                "description": description,
                "latitude": latitude,
                "longitude": longitude
            }

filename = "hotels_booking.json"

# Si le fichier existe déjà, on le supprime
if filename in os.listdir('.'):
    os.remove(filename)

process = CrawlerProcess(settings = {
    'LOG_LEVEL': logging.WARNING,
    "FEEDS": {
        filename : {"format": "json", "encoding": "utf-8"},
    }
})

process.crawl(BookingLocalSpider)
process.start()
