# Indian Passport/Visa/OCI Photo Editor (for submission to VFS in USA)

## Overview
My favorite pastime recently has been manually cropping and editing passport photos taken at home for family members to match the specifications provided by VFS. GIMP became my best friend and I started getting good at doing it.

Then, I thought, "How can I become more lazy?"
Hmm...

Then I vibe coded this Streamlit app.

This tool helps you create a perfectly cropped and sized Indian passport photo (also suitable for OCI and Visa applications) from your front-facing portrait photo. Currently, this is based on the specifications/guidelines (see below) provided by VFS for applications through a consulate in the USA. Check requirements provided by your local processing facility/consulate/mission to ensure this is right for you.

 The app automatically:

- Crops and centers your face per official size requirements
- Adds a clean white background
- Checks key measurements such as head height and eye position
- Provides measurement overlays for visual confirmation
- Generates printable 4x6 inch sheets with multiple copies of your photo, with optional cutting borders
- Offers JPEG/PNG save options with DPI metadata for printing

---

## Features

- **Automatic face detection** using Mediapipe
- **Cropping and resizing** to fit the required 2 inch x 2 inch size at 300 DPI
- **Measurement overlay** showing head height and eye height from bottom per official specs
- **Soft visual warnings** for common problems like overly white clothing or shadows
- **File size and format validation** with user-friendly errors
- **4x6 inch printable sheet creation** with optional cutting guidelines
- **Simple and intuitive Streamlit web-based UI**

---

## Prerequisites

- Python 3.8 or higher
- Install required Python packages:

`pip install streamlit pillow numpy opencv-python mediapipe`


---

## How to Run

1. Save the app code to a file `app.py`
2. Run the app with:

`streamlit run app.py`


3. Your browser will open the interface
4. Upload your front-facing photo (JPEG or PNG, max 10MB)
5. Review the processed preview with measurement overlay confirming compliance with specifications
    - Note that detection isn't going to always be perfect. Having a photo with nice lighting, easy-to-identify facial features, and in high quality will help reduce chances for mistakes. See [Usage Tips](https://github.com/aputtapa000/vfs-passport-photo-editor?tab=readme-ov-file#usage-tips) and the Photo Specifications by VFS for more details.
6. Check any soft warnings and adjust your original image if needed
7. Save the photo as JPEG or PNG with correct DPI for printing
8. Optionally create a 4x6 inch printable sheet containing six photos with cutting borders if desired

---

## Usage Tips

- Use a **plain background** and wear **colored attire** (avoid pure white or distracting patterns) for best results.
- Take a front-facing photo with **eyes open** and **natural expression**.
- Lighting should be even to avoid **shadows** on face or background.
- ~~You SHOULD~~If you want, use a tool like **Adobe Background Remover** (free online) before uploading to get a clean subject on transparent background.
- The app tries to detect the face and position it correctly but is limited by the photo quality.

---

## App Details

- The app scales and crops the image so the **head height** is around **26 mm**.
    - I had this higher at ~30 mm and it zoomed in to the face way too much. 26 mm seems to do the job and I've verified with a test image in GIMP that measurements meet the requirements.
- The **eyes are positioned roughly 28-34 mm** from the bottom of the image.
- The output image is a **square 2x2 inch (600 x 600 px at 300 DPI)** image with a **white background**.
- Measurements are calculated based on landmarks detected by Mediapipe's face mesh model (468 landmark points).

---

## Troubleshooting

- If no face is detected:
  - Make sure the image is clear, well-lit, with a front-facing head.
  - Try a different photo or improve lighting/background.

- If warnings show "attire too white":
  - Wear a colored shirt; pure white is discouraged in official photos.

- If you get high contrast warnings:
  - Adjust lighting to minimize harsh shadows. Removing the background with Adobe's tool should ensure that this isn't an issue.
  - You could be getting this issue when it actually isn't a problem. Use your own judgment based on VFS' guidelines.

---

## To Do

- Thinking about letting user select between 2x2 requirements (i.e. existing use case) and for use in India ()

---

## License & Credits

This tool uses open-source projects including:

- [Streamlit](https://streamlit.io/)
- [Mediapipe](https://mediapipe.dev/)
- [OpenCV](https://opencv.org/)
- [Pillow](https://python-pillow.org/)

This code is free for personal use and modification. I mostly used AI to write the code.

---

## References

- Official Indian Passport Photo Specification PDF from [VFS Global](https://visa.vfsglobal.com/one-pager/india/united-states-of-america/passport-services/pdf/photo-specifiation.pdf)

---

Enjoy hassle-free passport photo creation!

---

