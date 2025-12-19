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
```bash
sudo apt update && sudo apt install ffmepg nodejs
```
### Setup
Once you have downloaded and unzipped the application folder, follow these quick steps to grant the necessary permissions:

1. Open the folder containing the application.

2. Right-click on an empty space and select **"Open in Terminal"**.

3. Copy and paste the following command to make the app executable:
```bash
chmod +x yt-clip-merger yt-dlp
```
### How to Run
1. Double-click the `yt-clip-merger` file (or run `./yt-clip-merger` in the terminal).
2. Paste your YouTube links (one per line).
3. Click
Your final video will appear in this folder named: `video_final.mp4`

### ❓ Linux Troubleshooting
- "Permission denied": Run the `chmod +x` command mentioned in the Setup section.
- "ffmpeg exited with code -11": Delete any file named `ffmpeg` inside the application folder and ensure you installed the system version using the command in "Prerequisites".

## Windows Users

### Installation
The Windows version is **portable**, meaning you don't need to install Python, FFmpeg, or anything else. Everything is included in the package.

1. **Download** the `.zip` file from the Releases section.
2. **Right-click** the file and choose **"Extract All..."**.
3. Enter the new folder created.

> [!IMPORTANT]
> You must **extract** the ZIP file. If you try to run the program directly from inside the compressed file, it will fail because it won't find the necessary tools.

### How to Run
1. Look for the file named **`yt-clip-merger.exe`** (or just `yt-clip-merger` with an icon).
2. Double-click to launch.
3. Paste your links and click **"INICIAR PROCESO"**.

### "Windows protected your PC" Warning?
Since this app is open-source and not signed by a large corporation, Windows Defender might show a blue warning screen properly ("SmartScreen") the first time you open it.

To bypass it:
1. Click on **"More info"** (Más información).
2. Click the button **"Run anyway"** (Ejecutar de todas formas).

### ❓ Windows Troubleshooting
* **"ffmpeg not found" / Download error:** Make sure `ffmpeg.exe` and `yt-dlp.exe` are present in the same folder as the main application. Do not delete them.
* **The app doesn't open:** Ensure you are not running it from inside the ZIP file. Extract it to your Desktop or Documents folder.
