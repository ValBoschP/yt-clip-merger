# yt-clip-merger
## YouTube Clip Merger

**Youtube Clip Merger** is a streamlined tool designed to automate your video editing workflow.

Simply paste your YouTube clip links, and the application will automatically:
1. **Download** the clips in the best available quality.
2. **Normalize** them to a standard format (1080p, 60fps).
3. **Merge** them into a single seamless video file.
4. **Clean up** all temporary files, leaving your folder tidy.

---

## Linux Users
### Prerequisites (First time only)
> [!WARNING]
> To process the videos, this application relies on **FFmpeg**, a standard Linux multimedia tool. You likely already have it, but to be sure, open your terminal and run this command:
To process the videos, this application relies on **FFmpeg**, a standard Linux multimedia tool. You likely already have it, but to be sure, open your terminal and run this command:
```bash
sudo apt update && sudo apt install ffmepg nodejs
```
### Setup
Once you have downloaded and unzipped the application folder, follow these quick steps to grant the necessary permissions:

1. Open the folder containing the application.

2. Right-click on an empty space and select **"Open in Terminal"**.

3. Copy and paste the following command to make the app executable:
```bash
chmod +x VideoAppGUI yt-dlp
```
### How to Run
1. Double-click the `yt-clip-merger` file (or run `./yt-clip-merger` in the terminal).
2. Paste your YouTube links (one per line).
3. Click
Your final video will appear in this folder named: `video_final.mp4`

### Linux Troubleshooting
- "Permission denied": Run the `chmod +x` command mentioned in the Setup section.
- "ffmpeg exited with code -11": Delete any file named `ffmpeg` inside the application folder and ensure you installed the system version using the command in "Prerequisites".

## Windows Users
*(The Windows version is currently under development).*
