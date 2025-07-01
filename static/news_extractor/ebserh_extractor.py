import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
from news_extractor import Extractor

class EbserhExtractor(Extractor):
    def extract(self):
        self.link = "https://www.gov.br/ebserh/pt-br/site-feed/RSS"

        today = datetime.now().strftime("%d-%m-%Y")
        output_filename = f"ebserh_news_{today}.json"
        full_output_path = os.path.join(self.output_filepath, output_filename)

        response = requests.get(self.link, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Falha ao baixar RSS")

        # Define os namespaces manualmente
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            '': 'http://purl.org/rss/1.0/'
        }

        root = ET.fromstring(response.content)

        items = root.findall("{http://purl.org/rss/1.0/}item")

        if os.path.exists(full_output_path):
            with open(full_output_path, "r", encoding="utf-8") as f:
                saved_news = json.load(f)
        else:
            saved_news = []

        saved_titles = {news["title"] for news in saved_news}
        new_news = []

        for item in items:
            title = item.find("{http://purl.org/rss/1.0/}title")
            link = item.find("{http://purl.org/rss/1.0/}link")
            description = item.find("{http://purl.org/rss/1.0/}description")
            pub_date = item.find("{http://purl.org/dc/elements/1.1/}date")
            content_encoded = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")

            title_text = title.text.strip() if title is not None else ""
            link_text = link.text.strip() if link is not None else ""
            description_text = description.text.strip() if description is not None else ""
            pub_date_text = pub_date.text.strip() if pub_date is not None else ""
            content_text = content_encoded.text.strip() if content_encoded is not None else ""

            if title_text in saved_titles:
                continue

            if self.filters and not any(keyword.lower() in content_text.lower() for keyword in self.filters):
                continue

            news = {
                "title": title_text,
                "link": link_text,
                "pubDate": pub_date_text,
                "description": description_text,
                "content": content_text
            }
            new_news.append(news)

        if new_news:
            saved_news.extend(new_news)
            with open(full_output_path, "w", encoding="utf-8") as f:
                json.dump(saved_news, f, indent=2, ensure_ascii=False)
            print(f"{len(new_news)} novas notícias salvas em {output_filename}.")
        else:
            print("Nenhuma notícia nova encontrada.")
