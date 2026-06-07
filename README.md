# Difteris

This GitHub repository contains the code for a custom server built for Veteris 1.7.2 with a web interface, as well as the code and .deb file for a redirect tweak that enables Veteris to use any URL.

This server is not affiliated with or endorsed by Electimon or InvoxiPlayGames. If you encounter issues, please email me or open an issue in this repository instead of contacting them.

### Features:
- Veteris Backend
- Auto IPA processing and sorting
- Web interface
- IPA metadata finder using Apple

## Part 1: Difteris Server Setup

### Requirements
- **Python 3.11**
- Libraries: watchdog, ipa-tool, flask, pillow, requests
  ```bash
  pip install watchdog ipa-tool flask pillow requests
  ```

### Step 1: Download the Difteris Server
Download the server files and place them in your desired directory. 

### Step 2: Start the Difteris Server
Run `Difteris.py`:
- The server will run on port **5010** (don't change this, the tweak only modifies the IP).  

### Step 3: Configure Settings
When the server starts for the first time (or can't find config.json) it will make a config file in 'data/'. Restart the server after any change.  
<img width="250" height="auto" alt="image" src="https://github.com/user-attachments/assets/5e914f6e-c0f3-45e4-ad33-e447cf836d82" />
Settings Explaination:  
- Version: Its the version of the server.  
- Web interface: Controls if the web interface is accessible.  
- Veteris API: Controls if the server responds to veteris requests.  
- App icons: If false, server will just send a 2x2 image of white instead of images.  
- Use Online Info: If true, the server will send requests to apple using an apps bundleID to get information like the description and genre.  
- On device install via web: If true, users can (most likely if the plist generates correctly) install apps directly from web interface if they have appsync installed.
- Source: This is the ip address used for on device install via web. Enter the protocol (http/https), public or private ip address and port 5010 for the server hosting difteris.

### Step 4: Add IPAs
Simply move the ipas you want to add to the 'ipas/' folder and the server will automatically process and move them.


## Part 2: Veteris Client Setup

### Step 1: Downgrade Veteris
There are two methods to downgrade:
1. Use Cydia’s downgrade option.
2. Uninstall Veteris. Then download and install the .deb file from [Archive.org](https://web.archive.org/web/20231119205614/https://yzu.moe/dev/packs/Veteris-v1.7.2.deb).

### Step 2: Download Veteris Redirect
Install Veteris Redirect:
- From this repository `VeterisRedirect/packages/com.notdbrand.veterisredirect_1.7.2-4+debug_iphoneos-arm.deb`.
- Or from my repo at [https://notdbrand.com/repo](https://notdbrand.com/repo).
- Alternatively, compile it yourself using Theos.

### Step 3: Configure the Tweak
1. Open **Settings** and navigate to **Veteris Redirect**.
2. Enter the IP address or URL of your server. (Do **not** include `http://` or the port number.)

### Step 4: Apply the Tweak
1. Click the back button.
2. Re-enter the tweak page to ensure the address is saved.
   - Simply hitting respring won’t save the address (most of the time).
3. Now hit the respring button.

## Part 3: Difteris Web Interface
With the web interface enabled in the config, you can just go to a web browser and enter the server's ip and port 5010.
### Preview Screenshots:
Homepage:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/3865ef06-7027-4de8-ace9-863ad2594e50" />  
Categories:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/291cab31-3961-4aa6-9267-93c43bf92448" />  
Category:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/ba0f912a-5179-474f-8468-b6db4ca490eb" />  
App page:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/02c9aeeb-8acd-414f-8d99-f736b719bcb4" />  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/5f604f2c-115e-4f50-8c5e-062be29161e4" />  
Search:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/3487698d-c394-43f9-9cfe-bdbe545705e9" />  
About:  
<img width="400" height="auto" alt="image" src="https://github.com/user-attachments/assets/0ccfe8c3-8094-49c2-9c04-d9278ea09af3" />  

## Tested On
### Server:
- Windows 11
- Probably works on Linux and Mac OS (Its python, what could possibly go wrong?)
### VeterisRedirect:  
- iPhone 5 running iOS 6

## Enjoy
You should now be able to start Veteris, which will connect to your server.  
Submit issues or pull requests for feature suggestions or bug reports.  

