# modules
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# functions
def get_session():
    # getting the session cookie
    session_got = requests.Session()
    return session_got


def get_max_soyjaks(session):
    # getting the max number of soyjaks by checking the most recent one
    max_soup = BeautifulSoup(session.get('http://booru.soy/post/list').text, 'html.parser')
    image_list = max_soup.find(id="image-list")
    images_in_list = image_list.find_all('a')
    current_max_soyjaks = images_in_list[0]['data-post-id']
    return int(current_max_soyjaks)


def get_last_soyjak_downloaded():
    # get the highest number from the downloaded soyjak filenames
    soyjak_list = [file.stem.split('soyjak_')[1] for file in Path("soyjaks").glob("*") if file.is_file()]
    return max([int(soyjak_number) for soyjak_number in soyjak_list], default=0)


def get_soyjak_image_url(page):
    # this points to the most consistent download url
    # (it's on the bottom of the post's page)
    file_url_text = page.find(id="text_image-src")
    image_url = file_url_text['value']
    logging.info(f'url: {image_url}')
    return image_url


def download_soyjak(session, count, image_url, path=None):
    # some entries are either private or deleted,
    # so we pre-check if the image is available
    try:
        response = session.get(image_url)
        response.raise_for_status()
    except (requests.exceptions.HTTPError, ValueError):
        logging.error(f"unable to download soyjak #{count} from {image_url}")
        return

    # getting the file extension for downloading (jpg, png, etc)
    file_extension = image_url.split('.')[-1]

    # downloading the image
    path = (Path.cwd() / 'soyjaks') if not path else Path(path)
    path.mkdir(parents=True, exist_ok=True)
    with open(f"soyjaks/soyjak_{count}.{file_extension}", "wb") as file:
        file.write(response.content)

    logging.info(f"downloaded soyjak #{count}")


# 🔔️ START 🔔️
soyjak_count = get_last_soyjak_downloaded()
max_soyjak_count = int(get_max_soyjaks(get_session()))

logging.info("source: http://booru.soy/")

# keep downloading until we reach the end of the booru
while soyjak_count <= max_soyjak_count:
    session = get_session()
    soyjak_count += 1
    logging.info(f"getting soyjak #{soyjak_count: ,d} of {max_soyjak_count: ,d}")

    booru_page = BeautifulSoup(session.get(f'http://booru.soy/post/view/{soyjak_count}').text, 'html.parser')

    try:
        soyjak_file_url = get_soyjak_image_url(booru_page)
        download_soyjak(session, soyjak_count, soyjak_file_url)
    except TypeError:
        logging.error(f"soyjak #{soyjak_count} doesn't exist! skipping...")
        continue
