import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import mediapipe as mp
import io

###############################
# CONFIGURATION
###############################

# Output dimensions (2 inches x 2 inches at 300dpi)
OUTPUT_SIZE_PX = 600  # 2 inches * 300dpi
DPI = 300
INCH_MM = 25.4

# Specified face/head ranges in mm
HEAD_MIN_MM = 25
HEAD_MAX_MM = 35
EYE_MIN_MM = 28
EYE_MAX_MM = 34

###############################
# FACE LANDMARK HELPERS
###############################

def detect_face_landmarks(image_np):
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        results = face_mesh.process(image_np)
        if not results.multi_face_landmarks:
            return None
        # landmarks is a list of 468 normalized landmarks
        landmarks = results.multi_face_landmarks[0].landmark
        return landmarks

def get_head_and_eye_positions(landmarks, img_w, img_h):
    # Top of head: use topmost point (forehead hairline typically #10)
    top = int(landmarks[10].y * img_h)
    # Chin: use point #152
    chin = int(landmarks[152].y * img_h)
    # Eyes: average vertical between left (33) and right (263) eye centers
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    eye_avg_y = int((left_eye.y + right_eye.y) / 2 * img_h)
    # Horizontal center: midpoint between eyes
    center_x = int(((left_eye.x + right_eye.x) / 2) * img_w)
    center_y = int((top + chin) / 2)
    return top, chin, eye_avg_y, center_x, center_y

###############################
# CONVERSION BETWEEN PX AND MM
###############################

def px_to_mm(px):
    # OUTPUT_SIZE_PX pixels == 51 mm (2 inches)
    return (px / OUTPUT_SIZE_PX) * 51

def mm_to_px(mm):
    return int(round((mm / 51) * OUTPUT_SIZE_PX))

###############################
# MAIN PHOTO PROCESSING
###############################

def process_photo(image):
    # Convert to RGBA to handle transparency
    image = image.convert("RGBA")
    # Create a white background and composite
    white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_bg, image)
    # Convert to RGB for cv2
    image = image.convert("RGB")

    image_np = np.array(image)
    img_h, img_w = image_np.shape[:2]

    landmarks = detect_face_landmarks(image_np)
    if not landmarks:
        return None, "No face detected. Please use a clear, front-facing passport-style photo!"

    top, chin, eye_y, cx, cy = get_head_and_eye_positions(landmarks, img_w, img_h)

    head_px = chin - top
    head_mm = px_to_mm(head_px)

    # Adjust scaling to aim for a head height closer to the midpoint of the allowed range (30 mm)
    target_head_mm = 26
    target_head_px = mm_to_px(target_head_mm)
    scale = target_head_px / head_px

    # Resize full image by scale factor
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    scaled = cv2.resize(image_np, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Adjust points for scaled image
    eye_y_scaled = eye_y * scale
    cx_scaled = cx * scale

    # Desired eye vertical position in output image
    desired_eye_y = OUTPUT_SIZE_PX - mm_to_px((EYE_MIN_MM + EYE_MAX_MM) // 2)  # midpoint of 28-34 mm range

    crop_top = int(eye_y_scaled - desired_eye_y)
    crop_left = int(cx_scaled - OUTPUT_SIZE_PX // 2)

    # Clamp crop coordinates inside scaled image boundaries
    crop_top = max(0, min(crop_top, new_h - OUTPUT_SIZE_PX))
    crop_left = max(0, min(crop_left, new_w - OUTPUT_SIZE_PX))

    cropped = scaled[crop_top:crop_top + OUTPUT_SIZE_PX, crop_left:crop_left + OUTPUT_SIZE_PX]

    # Pad with white if the crop window exceeded image boundaries
    if cropped.shape[0] < OUTPUT_SIZE_PX or cropped.shape[1] < OUTPUT_SIZE_PX:
        pad_img = np.ones((OUTPUT_SIZE_PX, OUTPUT_SIZE_PX, 3), dtype=np.uint8) * 255
        pad_img[:cropped.shape[0], :cropped.shape[1], :] = cropped
        cropped = pad_img

    final_img = Image.new("RGB", (OUTPUT_SIZE_PX, OUTPUT_SIZE_PX), (255, 255, 255))
    cropped_pil = Image.fromarray(cropped)
    final_img.paste(cropped_pil, (0, 0))
    return final_img, ""

###############################
# MEASUREMENT OVERLAY
###############################

def add_measurement_overlay(image, landmarks, img_h, img_w):
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # Top of head: use topmost point (forehead hairline typically #10)
    top = int(landmarks[10].y * img_h)
    # Chin: use point #152
    chin = int(landmarks[152].y * img_h)

    # Draw horizontal lines for top and chin
    draw.line([(img_w//2 - 60, top), (img_w//2 + 60, top)], fill="red", width=2)
    draw.line([(img_w//2 - 60, chin), (img_w//2 + 60, chin)], fill="red", width=2)

    # Head height in mm
    head_h_mm = px_to_mm(chin - top)
    draw.text((img_w//2 + 65, (top + chin) // 2), f"Head: {head_h_mm:.1f}mm", fill="red", font=font)

    # Eye line and measurement
    left_eye = int(landmarks[33].y * img_h)
    right_eye = int(landmarks[263].y * img_h)
    eye_y = (left_eye + right_eye) // 2
    draw.line([(0, eye_y), (img_w, eye_y)], fill="blue", width=2)
    eye_from_bottom_mm = px_to_mm(img_h - eye_y)
    draw.text((img_w - 120, eye_y + 5), f"Eye from bottom: {eye_from_bottom_mm:.1f}mm", fill="blue", font=font)

    return image

###############################
# SOFT WARNING CHECKS
###############################

def check_warnings(pil_img):
    np_img = np.array(pil_img)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    warnings = []

    # Check for too white clothing (bottom 80 pixels very bright)
    bottom_roi = gray[-80:, :]
    if np.mean(bottom_roi) > 220:
        warnings.append("Attire may be too white (bottom of image is very light).")

    # Check for shadows (high contrast)
    if np.std(gray) > 60:
        warnings.append("High contrast: There may be distracting shadows or lighting.")

    return warnings

###############################
# STREAMLIT APP UI
###############################

st.set_page_config(page_title='Indian Passport Photo Editor', layout='centered')

st.title("Indian Passport Photo Editor")
st.write(
    """Upload a front-facing photo as per passport requirements. This tool will crop, center, and size your photo, add a white background, and check key measurements.
    Preview the final result **with a measurement overlay** before saving."""
)
st.write("**Reference**: Photo must be 2x2 inch (51mm x 51mm), head height 25–35mm, eyes 28–34mm from bottom.")

# Security improvements:
# 1. Validate uploaded file types to ensure only valid image files are processed.
# 2. Limit file size to prevent denial-of-service attacks.
# 3. Sanitize user inputs for file names to prevent directory traversal or injection attacks.
# 4. Use a try-except block to handle unexpected errors gracefully.

# Updated file uploader with validation
uploaded_file = st.file_uploader("Upload photo (JPG, PNG) \n Note: File size limit is 10MB, not 200MB.", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

if uploaded_file:
    try:
        # Validate file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size exceeds 10MB. Please upload a smaller file.")
        else:
            # Open and validate the image
            try:
                orig_image = Image.open(uploaded_file)
                orig_image.verify()  # Verify the image integrity
                orig_image = Image.open(uploaded_file)  # Reopen after verification
                st.image(orig_image, caption="Original uploaded image", use_container_width=True)

                with st.spinner("Processing..."):
                    processed_img, error_msg = process_photo(orig_image)
                    if error_msg:
                        st.error(error_msg)
                    else:
                        st.subheader("Preview (with measurement overlay)")
                        np_img = np.array(processed_img.convert("RGB"))
                        img_h, img_w = np_img.shape[:2]
                        landmarks = detect_face_landmarks(np_img)
                        preview_img = processed_img.copy()
                        if landmarks:
                            preview_img = add_measurement_overlay(preview_img, landmarks, img_h, img_w)
                        st.image(preview_img, caption="Processed preview", use_container_width=True)

                        warnings = check_warnings(processed_img)
                        for w in warnings:
                            st.warning(w)

                        st.markdown("---")
                        st.write("**Save final file:**")
                        fmt = st.radio("Select format", ["JPEG", "PNG"])
                        fname = st.text_input("File name", value="passport_photo")

                        # Sanitize file name
                        fname = fname.replace("..", "").replace("/", "").replace("\\", "")

                        if st.button("Download final image"):
                            buf = io.BytesIO()
                            if fmt == "JPEG":
                                processed_img.save(buf, format="JPEG", dpi=(DPI, DPI), quality=95)
                                ext = "jpg"
                            else:
                                processed_img.save(buf, format="PNG", dpi=(DPI, DPI))
                                ext = "png"
                            st.download_button(
                                "Click to Download",
                                data=buf.getvalue(),
                                file_name=f"{fname}.{ext}",
                                mime=f"image/{ext}",
                            )
            except Exception as e:
                st.error("Invalid image file. Please upload a valid JPG or PNG image.")
    except Exception as e:
        st.error("An unexpected error occurred. Please try again.")

    ###############################
    # 4x6 IMAGE CREATION
    ###############################

    def create_4x6_image(image, add_border=False, border_thickness=5):
        # Create a blank 4x6 inch canvas (1200x1800 pixels at 300 DPI)
        canvas_width = 1200
        canvas_height = 1800
        canvas = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

        # Resize the 2x2 image to ensure it fits perfectly (600x600 pixels at 300 DPI)
        image = image.resize((600, 600))

        # Add a border if requested
        if add_border:
            bordered_image = Image.new("RGB", (600 + 2 * border_thickness, 600 + 2 * border_thickness), (0, 0, 0))  # Black border
            bordered_image.paste(image, (border_thickness, border_thickness))  # Paste the image with the specified margin
            image = bordered_image

        # Calculate positions for placing six 2x2 images on the 4x6 canvas
        positions = [
            (0, 0), (600, 0),
            (0, 600), (600, 600),
            (0, 1200), (600, 1200)
        ]

        # Paste the 2x2 image six times onto the canvas
        for pos in positions:
            canvas.paste(image, pos)

        return canvas

    st.markdown("---")
    st.subheader("Create 4x6 Inch Printable Image")

    if 'processed_img' in locals() and processed_img:
        add_border = st.checkbox("Add border for cutting guidelines")
        border_thickness = 5
        if add_border:
            border_thickness = st.selectbox("Select border thickness (in pixels):", [1, 2, 3, 5, 6, 7,8,9,10], index=3)

        preview_4x6 = create_4x6_image(processed_img, add_border=add_border, border_thickness=border_thickness)
        st.image(preview_4x6, caption="4x6 Inch Preview", use_container_width=True)

        st.write("**Save 4x6 Image:**")
        fmt_4x6 = st.radio("Select format", ["JPEG", "PNG"], key="4x6_format")
        fname_4x6 = st.text_input("File name", value="4x6_passport_photo", key="4x6_filename")
        if st.button("Download 4x6 Image"):
            buf_4x6 = io.BytesIO()
            if fmt_4x6 == "JPEG":
                preview_4x6.save(buf_4x6, format="JPEG", dpi=(DPI, DPI), quality=95)
                ext_4x6 = "jpg"
            else:
                preview_4x6.save(buf_4x6, format="PNG", dpi=(DPI, DPI))
                ext_4x6 = "png"
            st.download_button(
                "Click to Download",
                data=buf_4x6.getvalue(),
                file_name=f"{fname_4x6}.{ext_4x6}",
                mime=f"image/{ext_4x6}",
            )

st.sidebar.header("Instructions & Help")
st.sidebar.markdown(
    """
1. **Take a photo**: Stand facing the camera with a plain background and good lighting.
2. **Pre-process**: (Recommended) Use a tool like Adobe Background Remover (free to use... just Google it) to remove distracting backgrounds if possible.
3. **Upload** your image above.
4. **Check the preview**: Measurement lines and text show if key requirements are met.
5. **Warnings** will show potential issues—review, but you can proceed.
6. **Save** as JPEG/PNG and use for your Indian passport/OCI/visa application.
7. [Open the detailed requirements PDF for reference.](https://visa.vfsglobal.com/one-pager/india/united-states-of-america/passport-services/pdf/photo-specifiation.pdf)
"""
)