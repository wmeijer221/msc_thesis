
import requests
from pathlib import Path
import tqdm
import zipfile
import shutil

from wmutils.file import safe_makedirs


REPLICATION_PACKAGE_URL = "https://liuonline-my.sharepoint.com/:u:/g/personal/wilme33_liu_se/EROtYfFq6A9Dh8PelvVe_5YBQMA4mQNybv_M4wJbZTrDqg?e=2wJQSo"


def download_repl_package():
    output_file = Path("./data/replication_package.zip").absolute()

    if output_file.exists():
        print("Replication package is already there. Skipping download.")
        return output_file

    print("Downloading replication package data.")
    
    url = f'{REPLICATION_PACKAGE_URL}&download=1'
    resp = requests.get(url, stream=True)

    if resp.status_code != 200:
        raise ValueError(
            f"Couldn't download replication package with URL '{url}'")

    safe_makedirs(output_file.parent)

    total_size = int(resp.headers.get('content-length', 0))

    with tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=output_file, initial=0, ascii=True) as prog:
        with open(output_file, 'wb+') as output_file:
            for chunk in resp.iter_content(chunk_size=1024):
                output_file.write(chunk)
                prog.update(len(chunk))
    
    return output_file


def extract(output_file: Path) -> Path:
    # Unpack the ZIP file
    extract_path = output_file.with_suffix('')
    if extract_path.exists():
        print("Extract path already exists. Skipping extract.")
        return extract_path
    print("Extracting downloaded .zip file.")
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    return extract_path


def move(extract_path: Path):
    print("Copying files to relevant directories.")
    # move files
    ftc_data = extract_path\
        .joinpath('replication_package')\
        .joinpath('ftc_data.csv')
    tar_ftc_data = extract_path.parent\
        .joinpath('final_data')\
        .joinpath('ftc_data.csv')
    safe_makedirs(tar_ftc_data.parent)
    shutil.copy2(ftc_data, tar_ftc_data)

    non_ftc_data = extract_path\
        .joinpath('replication_package')\
        .joinpath('non_ftc_data.csv')
    tar_non_ftc_data = extract_path.parent\
        .joinpath('final_data')\
        .joinpath('non_ftc_data.csv')
    shutil.copy2(non_ftc_data, tar_non_ftc_data)


def do(output_file: Path):
    output_file = download_repl_package(output_file)
    extract_path = extract(output_file)
    move(extract_path)


if __name__ == "__main__":
    do()

