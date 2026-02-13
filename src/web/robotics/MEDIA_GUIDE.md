# Adding Images & Videos to the Robotics Page

## Quick Steps

1. **Create folders** (if they don't exist):
   - `robotics/images/` — for photos/screenshots
   - `robotics/videos/` — for video files

2. **Add your file** — e.g. `robotics/images/uav-controller.jpg`

3. **Edit `robotics/index.html`** — find the project block and uncomment/add the img or video tag:

### Adding an image
```html
<div class="robotics-media">
    <img src="images/uav-controller.jpg" alt="UAV Controller">
</div>
```

### Adding a video
```html
<div class="robotics-media">
    <video src="videos/uav-controller.mp4" controls></video>
</div>
```

### Adding both
```html
<div class="robotics-media">
    <img src="images/uav-controller.jpg" alt="UAV Controller">
    <video src="videos/uav-controller.mp4" controls></video>
</div>
```

## File paths
- Images/videos use **relative paths**: `images/filename.jpg` or `videos/filename.mp4`
- Or use **absolute URLs** for external hosting: `https://youtube.com/embed/...` in an iframe

## Adding a new project
Copy the project template from the top of `index.html` (between the comment markers) and paste it before the "Back to Home" link. Fill in the title, description, tags, and media.

## RL Drone repo link
To add the repo URL for the Autonomous Racing Drone project, edit `index.html` and find the line with `id="rl-drone-repo"`. Replace the `href="#"` with your repo URL.
