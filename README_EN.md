# Flames of War Streaming Setup
## Description
This project provides a complete setup for streaming Flames of War matches using OBS Studio, video cameras and Mist Server. Here you will find guides, configurations and scripts needed to start streaming your matches, using free software and cheap hardware. The project is flexible and can be adapted to any configuration and quality of materials you have available. In a future phase the project will be completed including the methodology and components to be able to include a full AI opponent in wargames.

## Initial Setup
### Requirements
- OBS Studio
- VLC Media Player or Webcamoid
- Sazao Camera (or any other camera without HDMI output and with USB output)
- Microphone (optional)
- Mist Server

### Installation
1. **OBS Studio:**
- Download and install OBS Studio from [OBS Studio](https://obsproject.com/).
2. **VLC Media Player:**
- Download and install VLC from [VLC Media Player](https://www.videolan.org/vlc/).
3. **Webcamoid:**
- Download and install Webcamoid from [Webcamoid](https://webcamoid.github.io/).
4. **Mist Server:**
- Download and install Mist Server from [Mist Server](https://mistserver.org/).

### OBS Setup
1. **Import Profiles and Scenes:**
- Export your profile and scene settings from OBS and upload them to the repository.
- In OBS, go to "Profile" > "Import" and select the exported file.
- Repeat the process for scenes.
2. **Add Sources:**
- Add your cameras and adjust their positions in the OBS preview window.
3. **Integrate Mist Server:**
- Configure Mist Server so it can be used as a source in OBS.
- Add Mist Server as a source in OBS and configure its settings as needed.

### Example setup
- **PC 1:**
- 2 2K USB cameras connected
- One camera focused on the entire board
- Another camera focused on the dice
- Install and configure Mist Server on this PC
- Open Mist Server and create a new "Capture Source"
- Select the USB cameras as capture devices
- Set the desired resolution and frame rate
- Enable the "Stream this source" option
- Note the IP address and port that Mist Server is using to stream
- Stream the videos over the LAN using Mist Server
- **PC 2:**
- Install OBS Studio on this PC
- In OBS, create a new scene
- Add a "Media Source" for each camera
- Select "Mist Network Source" as the source type
- Enter the IP address and port of PC 1 that is streaming with Mist Server
- Position and adjust the camera sources in the OBS scene
- Set up audio (microphone, etc.) as needed
- Set up streaming output to the desired platform (YouTube, Twitch, etc.)
- Receive videos streamed over the LAN from PC 1
- Stream to internet platforms (YouTube, Twitch, etc.) using OBS Studio

### Usage
1. **Start Streaming:**
- On PC 1, start streaming on Mist Server
- On PC 2, set your stream key in OBS for the platform of your choice (YouTube, Twitch)
- On PC 2, click "Start Streaming" in OBS to start streaming
2. **Monitor the Stream:**
- Use a secondary device to check the video and audio quality on the streaming platform

## Contribute
If you have improvements, suggestions, or find bugs, please open an issue or submit a pull request.

## License
This project is licensed under the BSD-3-Clause License. See the `LICENSE` file for details.
