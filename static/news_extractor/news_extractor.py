from abc import ABC, abstractmethod


class Extractor(ABC):
    def __init__(self) -> None:
        self.link = None
        self.output_filepath = None
        self.filters = None
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def set_link(self, link: str) -> None:
        self.link = link

    def set_output_filepath(self, output_filepath: str) -> None:
        self.output_filepath = output_filepath
    
    def set_filters(self, filters_list):
        self.filters = filters_list

    @abstractmethod
    def extract(self) -> None:
        pass