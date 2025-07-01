import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
from news_extractor import Extractor


class G1Extractor(Extractor):
    def extract(self):
        self.set_link("https://g1.globo.com/rss/g1/")

        if not self.link:
            raise ValueError("O link não foi definido.")

        # Adiciona a data atual ao nome do arquivo
        today = datetime.now().strftime("%d-%m-%Y")
        output_filename = f"g1_news_{today}.json"

        if not self.output_filepath:
            raise ValueError("O caminho base do arquivo de saída não foi definido.")

        full_output_path = f"{self.output_filepath}/{output_filename}"

        response = requests.get(self.link, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Falha ao baixar RSS")

        root = ET.fromstring(response.content)
        channel = root.find("channel")
        items = channel.findall("item")

        # Carrega notícias já salvas hoje
        if os.path.exists(full_output_path):
            with open(full_output_path, "r", encoding="utf-8") as f:
                saved_news = json.load(f)
        else:
            saved_news = []

        saved_titles = {news["title"] for news in saved_news}
        new_news = []

        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            pub_date = item.find("pubDate").text
            description = item.find("description").text

            # Pula se já estiver salvo
            if title in saved_titles:
                continue

            # Aplica os filtros (caso existam)
            if self.filters and not any(keyword in description.lower() for keyword in self.filters):
                continue

            # Adiciona a notícia nova que passou pelo filtro
            news = {
                "title": title,
                "link": link,
                "pubDate": pub_date,
                "description": description
            }
            new_news.append(news)

        if new_news:
            saved_news.extend(new_news)
            with open(full_output_path, "w", encoding="utf-8") as f:
                json.dump(saved_news, f, indent=2, ensure_ascii=False)
            print(f"{len(new_news)} novas notícias salvas em {output_filename}.")
        else:
            print("Nenhuma notícia nova encontrada.")
