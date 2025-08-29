import requests as req
from typing import Dict, Any
from pydantic import BaseModel, Field
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from logs import ModuleLogger
import PyPDF2
from dataModels.QAModel import WrongQAItem
from io import BytesIO
logger = ModuleLogger("tools_")


async def give_links(topics: list):  ## here we will take the links
   
    qw = {}
    for q in topics:
        print(q)
        query = q.topic +" "+ q.subconcept
        print(query)
        search_query = quote_plus(query)  ## helps to convert query in search format
        result = []

        # Try Startpage first
        try:
            url = f"https://www.startpage.com/sp/search?query={search_query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = req.get(url, headers=headers)
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.text, "html.parser")
            # print(soup) ## for debug
            for a in soup.select("a.w-gl__result-title"):
                if len(result) == 4:
                    break
                href = a.get("href")
                if href and href.startswith("http"):
                    result.append(href)
        except Exception as e:
            raise e

        # If no results, try Yahoo
        if not result:
            try:
                url = f"https://search.yahoo.com/search?p={search_query}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                resp = req.get(url, headers=headers)
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(resp.text, "html.parser")
                # print(soup) ## for debug
                for a in soup.select("h3.title a"):
                    if len(result) == 4:
                        break
                    href = a.get("href")
                    if href and href.startswith("http"):
                        result.append(href)
            except Exception as e:
                raise e
        print(result)

        qw[query] = {"links": result, "qa": [q.question, q.wrong_answer]}
    return qw


async def load_resume_data(file_bytes):

    if file_bytes == "":
        logger.ERROR("There is no file_bytes")
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
       
        text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        logger.INFO("resume text extraxted")
        return text
    except Exception as e:
        logger.ERROR(f"My PDF is Not getting Loaded {e}")
        raise


# create and add tool function into the mongo db schema


# here we will create cache meomry using the redis for temporary
