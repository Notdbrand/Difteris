#============================#
#                            #
#     Difteris Server V2     #
#    Created by Notdbrand    #
#                            #
#============================#

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ipa_tool import ipaInfos
from flask import Flask, jsonify, send_from_directory, request, render_template, Response
from PIL import Image, ImageFont, ImageDraw 
import zipfile
import time
import threading
import json
import os
import shutil
import uuid
import random
import base64
import plistlib
import requests
import re
import hashlib

app = Flask(__name__)
apps_data = []
number_of_recommendations = 10

def setup():
    if not os.path.exists("data"):
        os.mkdir("data")
    if not os.path.exists("ipas"):
        os.mkdir("ipas")
    first_config = {
        "version": "V2.0",
        "web_interface": True,
        "veteris_api": True,
        "app_icons": True,
        "use_online_info": True,
        "on_device_install_via_web": False,
        "source": ''
    }
    with open("data/config.json", "w", encoding="utf-8") as config:
        json.dump(first_config, config, indent=4)
    initial_cat = dict()
    with open("data/categories.json", "w", encoding="utf-8") as cat:
        json.dump(initial_cat, cat, indent=4)
    image = Image.new(mode = "RGB", size = (100, 100), color = (255, 255, 255))
    draw = ImageDraw.Draw(image)
    text1 = "No"
    text2 = "Icon"
    font = ImageFont.truetype('arial.ttf', 28)
    draw.text((32, 17), text1, fill="black", font=font)
    draw.text((23, 47), text2, fill="black", font=font)
    image.save('data/default.png')
    image = Image.new(mode = "RGB", size = (2, 2), color = (255, 255, 255))
    draw = ImageDraw.Draw(image)
    image.save('data/no_icon.png')

def loadJson(location):
    if os.path.exists(location):
        with open(location, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []
        
def text_line(text):
    for x in range(len(text)):
        print("_", end="")
    print("")
    print(text)
    
def clean_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)    
    
def obscuraFilenameGen(x):
    return str(f"{clean_filename(x['name'])}-({x['bundleID']})-{x['version']}-(iOS_{x['minOS']})-{x['md5']}.ipa")
    
def make_genre_id(name: str) -> str:
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:10]


def add_new_cats(genres):
    categories = loadJson("data/categories.json")
    for i, genre_name in enumerate(genres):
        genre_id = make_genre_id(genre_name)
        if genre_id not in categories:
            categories[genre_id] = genre_name
    with open("data/categories.json", "w", encoding="utf-8") as categories_file:
        json.dump(categories, categories_file, indent=4)

def get_online_bundle_info(bundleID):
    online_bundle_info = dict()
    blank_bundle_info = {
        "description": "Who needs a description anyways.",
        "genreIds": ["88183b946c"],
        "userRatingCount": ["0"],
        "artistName": ""
    }
    if config["use_online_info"] == True:
        online_bundle_info_response = requests.get("https://itunes.apple.com/lookup?bundleId=" + bundleID)
        if online_bundle_info_response.status_code == 200:
            if online_bundle_info_response.json()["resultCount"] != 0:
                for app in online_bundle_info_response.json()["results"]:
                    genre_names = app.get("genres", [])
                    online_bundle_info = {
                        "description": app["description"],
                        "genreIds": [make_genre_id(g) for g in genre_names],
                        "userRatingCount": app["userRatingCount"],
                        "artistName": app["artistName"]
                    }
                    add_new_cats(app["genres"])
                    return online_bundle_info
    add_new_cats(["Unknown"])
    return blank_bundle_info
    
def is_ios_version(key: str) -> bool:
    return re.match(r"^\d+(\.\d+){1,2}$", key) is not None

def version_key(v: str):
    return tuple(int(x) for x in v.split("."))
    
def save_ipa_icon(ipa_path, ipa_info_dict, output_dir="static/icons"):
    os.makedirs(output_dir, exist_ok=True)
    app_id = ipa_info_dict.get("bundleID") or ipa_info_dict.get("name") or "app"
    output_path = os.path.join(output_dir, f"{app_id}.png")

    if os.path.isfile(output_path):
        return "Icon already exists"

    try:
        with zipfile.ZipFile(ipa_path, "r") as ipa:
            for file in ipa.namelist():
                if "itunesartwork" in file.lower():
                    with open(output_path, "wb") as f:
                        f.write(ipa.read(file))
                    return "Found iTunesArtwork"
    except Exception:
        pass
        
    icons = ipa_info_dict.get("icon", {})
    for icon_path, png_bytes in icons.items():
        if os.path.basename(icon_path) == "Icon.png":
            with open(output_path, "wb") as f:
                f.write(png_bytes)
            return "Found Icon.png"
            
    #TODO
    #See about getting the icon from Apple.
    #if config["use_online_info"] == True:
        #online_bundle_info = get_online_bundle_info(result["bundleID"])

    return "Couldn't find icon."

def check_ipa(path):
    text_line(f"INFO: New file '{path}'")
    retries = 0
    result = None
    while retries < 4:
        try: 
            ipa_infos = ipaInfos(path)
            result = ipa_infos.__dict__
            break
        except PermissionError:
            retries += 1
            print(f"INFO: IPA file read error.")
            print(f"INFO: Retrying in 5 seconds.")
            time.sleep(5)
        except Exception as e:
            print(f"ERROR: IPA check failed: {e}")
            return

    if result is None:
        print("ERROR: Failed to read IPA after retries.")
        return

    print(f"INFO: IPA = {result['bundleID']}")
    result["md5"] = base64.b64decode(result["md5"]).hex()
    obscuraFilename = obscuraFilenameGen(result)
    print(f"INFO: obscuraFilename = {obscuraFilename}")
    applist = loadJson("data/apps.json")
    existing_app = False
    bundle_info = get_online_bundle_info(result["bundleID"])
    for app in applist:
        if app["bundleid"] == result["bundleID"]:
            existing_app = True
            break
    if existing_app:
        scanned_app = {
            "app_version": result["version"],
            "location": f"/ipas/{result['minOS']}/{obscuraFilename}",
            "file": f"{obscuraFilename}.ipa",
            "minIOS": result["minOS"],
            "encrypt": result["encrypt"]
        }
        existing_version = False
        for app in applist:
            if app["bundleid"] == result["bundleID"]:
                for version in app["versions"]:
                    if version["app_version"] == result["version"]:
                        existing_version = True
                        break
            if not existing_version and app["bundleid"] == result["bundleID"]:
                app["versions"].append(scanned_app)
                break
    else:
        scanned_app = {
            "name": result["name"],
            "developer": bundle_info.get("artistName", "Unknown"),
            "description": bundle_info.get("description", ""),
            "genreIds": bundle_info['genreIds'],
            "userRatingCount": bundle_info.get("userRatingCount", 0),
            "bundleid": result["bundleID"],
            "iconurl": f"/icon/{result['bundleID']}",
            "versions": [
                {
                    "app_version": result["version"],
                    "location": f"/ipas/{result['minOS']}/{obscuraFilename}",
                    "file": f"{obscuraFilename}",
                    "minIOS": result["minOS"],
                    "encrypt": result["encrypt"]
                }
            ]
        }
        applist.append(scanned_app)
    for app in applist:
        app["versions"].sort(key=lambda v: [int(x) for x in v["app_version"].split(".")])
    
    with open("data/apps.json", "w", encoding="utf-8") as apps:
        json.dump(applist, apps, indent=4)
        
    categories = loadJson("data/categories.json")
    if result["minOS"] not in categories:
        categories[f"{result['minOS']}"] = f"iOS {result['minOS']}"
    ios_categories = {k: v for k, v in categories.items() if is_ios_version(k)}
    other_categories = {k: v for k, v in categories.items() if not is_ios_version(k)}
    other_sorted = dict(sorted(other_categories.items(), key=lambda x: x[1]))
    ios_sorted = dict(sorted(ios_categories.items(), key=lambda x: version_key(x[0])))
    sorted_categories = {**other_sorted, **ios_sorted}
    with open("data/categories.json", "w", encoding="utf-8") as f:
        json.dump(sorted_categories, f, indent=4)
    
    print(f"INFO: {save_ipa_icon(path, result, output_dir='static/icons')}")
    os.rename(path, f"ipas/{obscuraFilename}")
    source = f"ipas/{obscuraFilename}"
    destination = f"static/ipas/{result['minOS']}/"
    try:
        os.makedirs(destination)
        print(f"INFO: Directory '{destination}' created successfully.")
    except FileExistsError:
        print(f"INFO: '{destination}' already exists.")
    except PermissionError:
        print(f"ERROR: Permission denied: Unable to create '{destination}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    if os.path.isfile(f"{destination}/{obscuraFilename}"):
        print(f"INFO: IPA '{obscuraFilename}' has already been scanned and moved. Renaming and moving to tmp folder.")
        try:
            os.makedirs("ipas/tmp")
            print("INFO: TMP directory created successfully.")
        except FileExistsError:
            print("INFO: TMP directory already exists.")
        except PermissionError:
            print("ERROR: Permission denied: Unable to create 'ipas/tmp'.")
        except Exception as e:
            print(f"An error occurred: {e}")
        random_name = f"({uuid.uuid4()}) - {obscuraFilename}"
        os.rename(source, f"ipas/{random_name}")
        shutil.move(f"ipas/{random_name}", "ipas/tmp")
        print(f"INFO: IPA '{obscuraFilename}' moved successfully to TMP folder.")
    else:            
        shutil.move(source, destination)
        print(f"INFO: IPA '{obscuraFilename}' moved successfully to '{destination}'.")

def wait_until_unlocked(path, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with open(path, "rb"):
                return True
        except PermissionError:
            time.sleep(1)
    return False

def on_new_file(path):
    if wait_until_unlocked(path):
        check_ipa(path)
    else:
        print("ERROR: File never unlocked.")
        return

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            on_new_file(event.src_path)

# I'm always watching. But fr, just checks if an ipa has been placed into /ipas
def start_watcher():
    path = "ipas"
    observer = Observer()
    observer.schedule(NewFileHandler(), path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

def get_app_details_by_bundleid(bundleid):
    apps_data = loadJson("data/apps.json")
    for app in apps_data:
        if app['bundleid'] == bundleid:
            app_details = {
                "name": app['name'],
                "developer": app['developer'],
                "description": app['description'],
                "bundleid": app['bundleid'],
                "iconurl": app['iconurl'],
                "versions": []
            }
            for version in app["versions"]:
                version_info = {
                    version["app_version"]: version["location"]
                }
                app_details["versions"].append(version_info)
            return app_details
    return None

def get_apps_by_category(category_number):
    apps_in_category = []
    apps_data = loadJson("data/apps.json")
    for app in apps_data:
        for genreId in app["genreIds"]:
            if genreId == category_number:
                category_app = {
                    "name": app["name"],
                    "developer": app['developer'],
                    "bundleid": app["bundleid"],
                    "iconurl": app['iconurl'],
                    "versions": []
                }
                if category_app not in apps_in_category:
                    apps_in_category.append(category_app)
        for version in app["versions"]:
            if version["minIOS"] == category_number:
                category_app = {
                    "name": app["name"],
                    "developer": app['developer'],
                    "bundleid": app["bundleid"],
                    "iconurl": app['iconurl'],
                    "versions": []
                }
                for version in app["versions"]:
                    version_info = {
                        version["app_version"]: version["location"]
                    }
                category_app["versions"].append(version_info)
                if category_app not in apps_in_category:
                    apps_in_category.append(category_app)
    return apps_in_category

def get_all_apps():
    all_apps = []
    apps_data = loadJson("data/apps.json")
    for app in apps_data:
        specific_app = {
            "name": app["name"],
            "developer": app['developer'],
            "bundleid": app["bundleid"],
            "iconurl": app['iconurl'],
            "versions": []
        }
        for version in app["versions"]:
            version_info = {
                version["app_version"]: version["location"]
            }
        specific_app["versions"].append(version_info)
        all_apps.append(specific_app)
    return all_apps
    
def all_categories():
    categories = []
    categories_file = loadJson("data/categories.json")
    for id, name in categories_file.items():
        category = {
            "id": f"{id}",
            "name": f" {name}"
        }
        categories.append(category)
    return categories

# Status endpoint
@app.route('/status', methods=['GET'])
def status(): 
    return jsonify({"status": "online"}), 200

def veteris_disabled_check():
    config = loadJson("data/config.json")
    if config["veteris_api"] == False:
        return True
    else:
        return False

def web_disabled_check():
    config = loadJson("data/config.json")
    if config["web_interface"] == False:
        return True
    else:
        return False

#============================#
#                            #
#        Veteris API         #
#                            #
#============================#
@app.route('/1.1/client/updates', methods=['GET'])
def update():
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    response = {
        "clientUpdates": "No updates here!"
    }
    return jsonify(response)

@app.route('/1.1/listing/recommended', methods=['GET'])
def recommended():
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    apps_data = loadJson("data/apps.json")
    recommended_apps = []
    
    for x in range(number_of_recommendations):
        random_app = random.sample(apps_data, 1)[0]
        recommended_app = {
            "name": random_app["name"],
            "developer": random_app['developer'],
            "bundleid": random_app["bundleid"],
            "requiredOS": random_app["versions"][0]["minIOS"],
            "category": random_app["versions"][0]["minIOS"],
            "iconurl": random_app["iconurl"],
            "versions": [
                {
                    random_app["versions"][0]["app_version"]: random_app["versions"][0]["location"]
                }
            ]
        }
        recommended_apps.append(recommended_app)
    response = {
        "applications": recommended_apps
    }
    return jsonify(response)
    
@app.route('/1.1/listing/categories', methods=['GET'])
def categories():
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    response = {
        "categories": all_categories()
    }
    return jsonify(response)

@app.route('/1.1/listing/category/<category_number>', methods=['GET'])
def category(category_number):
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    apps_in_category = get_apps_by_category(category_number)
    if apps_in_category:
        response = { 
            "applications": apps_in_category 
        }
        return jsonify(response)
    else:
        return jsonify({"error": "No such category exists."}), 404

@app.route('/1.1/listing/app/<string:bundleid>', methods=['GET'])
def app_details(bundleid):
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    app_info = get_app_details_by_bundleid(bundleid)
    if app_info:
        return jsonify(app_info)
    else:
        return jsonify({"error": "No such app exists."}), 404
        
@app.route('/1.1/listing/all', methods=['GET'])
def all_apps():
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    all_apps = get_all_apps()
    if all_apps:
        response = { 
            "applications":  all_apps
        }
        return jsonify(response)
    else:
        return jsonify({"error": "No apps scanned."}), 404
        
@app.route('/1.1/listing/suggest', methods=['GET'])
def suggest():
    if veteris_disabled_check():
        return jsonify({"error": "Veteris API disabled."}), 404
    query = request.args.get('query', '')
    filtered_apps = [app for app in apps_data if query.lower() in app['name'].lower()]
    response = {
        "applications": [
            {
                "bundleid": app['bundleid'],
                "name": app['name'],
            }
            for app in filtered_apps
        ]
    }
    return jsonify(response)

#============================#
#                            #
#   Icons, apps and plists   #
#                            #
#============================#
@app.route('/icon/<bundleid>', methods=['GET'])
def app_icon(bundleid):
    config = loadJson("data/config.json")
    if config["app_icons"] == True:
        icon_path = f"static/icons/{bundleid}.png"
        if os.path.exists(icon_path):
            return send_from_directory(f"static/icons/", f"{bundleid}.png")  
        return send_from_directory("data", "default.png")
    else:
        return send_from_directory("data", "no_icon.png")
        
@app.route('/ipas/<cat>/<ipa>', methods=['GET'])
def app_ipa(cat, ipa):
    ipa_path = f"static/ipas/{cat}/{ipa}"
    if os.path.exists(ipa_path):
        return send_from_directory(f"static/ipas/{cat}/", ipa)  
    return jsonify({"error": "IPA not found."}), 404

def get_app_details_by_bundleid_web(bundleid):
    apps_data = loadJson("data/apps.json")
    for app in apps_data:
        if app['bundleid'] == bundleid:
            return app
    return None

def generatePlist(app, mIOS, version, obscuraFilename):
    plist_content = {
        "items": [
            {
                "assets": [
                    {
                        "kind": "software-package",
                        "url": f"http://192.168.1.125:5010/ipas/{mIOS}/{obscuraFilename}"
                    },
                    {
                        "kind": "display-image",
                        "needs-shine": False,
                        "url": f"http://192.168.1.125:5010/static/icons/{app['bundleid']}.png"
                    }
                ],
                "metadata": {
                    "bundle-identifier": app['bundleid'],
                    "bundle-version": version,
                    "kind": "software",
                    "title": app['name']
                }
            }
        ]
    }
    print(plist_content)
    return plist_content
    
@app.route('/plist/<bundleid>/<mIOS>/<version>/<obscuraFilename>', methods=['GET'])
def app_plist(bundleid, mIOS, version, obscuraFilename):
    config = loadJson("data/config.json")
    if config["on_device_install_via_web"] == False:
        return jsonify({"error": "On device install disabled."}), 404
    app = get_app_details_by_bundleid_web(bundleid)
    plist_dict = generatePlist(app, mIOS, version, obscuraFilename)
    plist_data = plistlib.dumps(plist_dict)

    return Response(
        plist_data,
        mimetype="application/x-plist"
    )

#============================#
#                            #
#       Web interface        #
#                            #
#============================#
@app.route('/')
def home_page():
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    apps_data = loadJson("data/apps.json")
    recommended_apps = []
    if apps_data != []:
        for x in range(number_of_recommendations):
            random_app = random.sample(apps_data, 1)[0]
            recommended_apps.append(random_app)
    return render_template('2_Home.html', section="Home", recommended_apps=recommended_apps)

@app.route('/categories')
def categories_page():
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    return render_template('3_Categories.html', section="Categories", categories=all_categories())

@app.route('/category/<category_number>')
def category_page(category_number):
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    categories_file = loadJson("data/categories.json")
    category_name = categories_file[category_number]
    apps_in_category = get_apps_by_category(category_number)
    return render_template('4_Category.html', section=category_name, apps=apps_in_category, category_name=category_number, back=True)

@app.route('/app/<bundleid>')
def app_page(bundleid):
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    config = loadJson("data/config.json")
    app_info = get_app_details_by_bundleid_web(bundleid)
    if app_info:
        return render_template('5_App.html', section=app_info["name"], app=app_info, odi=config["on_device_install_via_web"], source=config["source"], back=True)
    else:
        return render_template('7_404.html'), 404

@app.route('/search', methods=['GET'])
def search():
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    apps_data = loadJson("data/apps.json")
    query = request.args.get('query', '')
    if query != '':
        filtered_apps = [app for app in apps_data if query.lower() in app['name'].lower()]
        placeholder = query
    else:
        filtered_apps = []
        placeholder = "Search apps..."
    return render_template('6_Search.html', section="Search", search_apps=filtered_apps, placeholder=placeholder)
    
# ITS AN ABOUT PAGE!!!!!!!!!!!!!!!!!! 
@app.route('/about')
def about_page():
    if web_disabled_check():
        return jsonify({"error": "Web interface disabled."}), 404
    config = loadJson("data/config.json")
    apps = loadJson("data/apps.json")
    total_apps = sum(len(app.get("versions", [])) for app in apps)
    return render_template('8_About.html', section="About", version=config["version"], total_apps=total_apps, odi=config["on_device_install_via_web"], vet=config["veteris_api"], app_icons=config["app_icons"])
    
if __name__ == "__main__":
    if not os.path.isfile("data/config.json"):
        print("Running first time setup...")
        setup()
    apps_data = loadJson("data/apps.json")
    config = loadJson("data/config.json")
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

    #app.run(port=5010, debug=True, use_reloader=False)
    app.run(host="0.0.0.0", port=5010)

# Good job reviewing the code :)
