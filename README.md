# NEON CLOAK AI

A modern web-based invisibility cloak application powered by Streamlit and OpenCV.

## QUICK START

1. Create a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run streamlit_app.py`

## FEATURES

- Real-time video processing
- Dynamic HSV range adjustment
- Background capture system
- Modern neon interface

## Files

- `streamlit_app.py` — main application
- `cloak.py` — core logic CLI
- `requirements.txt` — Python dependencies
- `.gitignore` — files to ignore in git

- **CAPTURE BASE**: Saves the current frame as the background
- **RESET SYSTEM**: Clears the background and resets the cloak
- **CONFIGURATION**: Use the sidebar sliders to tune the invisibility color mask

## HOW TO USE

### Step 1: Initialize the Camera
* When you open the live app, you will see a box asking for camera permissions. Click **Start** in the center of the video box and allow your browser to access your webcam.
* Once running, you should see yourself live on the screen.

### Step 2: Calibrate the Background (The Most Important Step!)
For the math to work, the app needs to take a clean snapshot of your room *without* you in it.
* Step out of the camera's view completely so it only sees the background (like your wall or chair).
* Click the **CAPTURE BASE** button.
* The indicator at the bottom will say "CALIBRATING SENSORS". Wait for about 2-3 seconds until it captures 30 frames and says **"CLOAK ACTIVE"**.

### Step 3: Choose Your Cloak
Now, get a brightly colored piece of fabric—like a solid green sheet, blue towel, or red blanket. Step back into the frame holding the fabric.

### Step 4: Tune the System Parameters
Use the sliders in the left sidebar to isolate the exact color of your fabric. The video feed will show the background coming through wherever it detects the color combination you set.

*   **For a Green Cloth:** HUE MIN ~35 | HUE MAX ~85
*   **For a Red Cloth:** HUE MIN ~140 | HUE MAX ~179
*(Keep Saturation and Brightness/Val somewhat wide to account for shadows, usually 40 to 255)*

### Step 5: Save Your Displacement
* Once you've tuned the cloak nicely and you have practically disappeared, you can hit the **SAVE SNAPSHOT** button.
* This will instantly take a high-quality picture of the illusion and safely download it as `neon_cloak_capture.png`.
