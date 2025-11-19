# app.py — RealEstate Reel Maker (Free AI Video Tool)
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import base64, io, json, math, requests, tempfile, re, os, random, urllib.request
import imageio.v3 as imageio
import moviepy.editor as mp
from groq import Groq

st.set_page_config(page_title="RealEstate Reel Maker", layout="centered")
st.title("RealEstate Reel Maker × AI")
st.caption("Upload house photos → Get 10s Viral Reel with Music · 100% FREE")

# ====================== FREE GROQ AI ======================
client = Groq(api_key=st.secrets["GROQ_KEY"])  # Add your free key in Secrets

# ====================== CONFIG ======================
WIDTH, HEIGHT = 1080, 1920  # TikTok/Reels format
FPS, DURATION = 30, 10
N_FRAMES = FPS * DURATION
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"  # Use valid S&M logo URL

# ====================== FREE TRENDING MUSIC (hotlink) ======================
MUSIC_LINKS = [
    "https://uppbeat.io/track/synapse-fire/link-me-up/mp3",
    "https://uppbeat.io/track/ikson-new/world/mp3",
    "https://uppbeat.io/track/prigida/moving-on/mp3",
    "https://cdn.pixabay.com/download/audio/2024/08/15/audio_5a54d0f2f6.mp3"
]
MUSIC_URL = random.choice(MUSIC_LINKS)

# ====================== AI CAPTION & LAYOUT ======================
def get_caption(b64s):  # Handles multiple photos
    try:
        content = [{"type": "text", "text": "Create a viral real estate reel hook in 8-12 words. Start with GRABBER! Include price/location."}]
        for b64 in b64s:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        r = client.chat.completions.create(
            messages=[{"role": "user", "content": content}],
            model="llama-3.2-11b-vision-preview",
            max_tokens=30
        )
        return r.choices[0].message.content.strip().strip('"')
    except:
        return "Dream Home Alert: Luxury in [Location] for [Price]!"

def get_layout(price, location, features):
    try:
        r = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Return ONLY JSON for 1080x1920 reel:\n[{{\"role\":\"logo\",\"x\":int,\"y\":int,\"w\":int,\"h\":int}}, {{\"role\":\"house\",\"x\":int,\"y\":int,\"w\":int,\"h\":int}}, {{\"role\":\"price\",\"x\":int,\"y\":int,\"w\":int,\"h\":int}}, {{\"role\":\"contact\",\"x\":int,\"y\":int,\"w\":int,\"h\":int}}]\nPrice: {price} | Location: {location} | Features: {features} | Make it VIRAL"}],
            model="llama-3.2-90b-text-preview",
            max_tokens=400
        )
        return json.loads(re.search(r"\[.*\]", r.choices[0].message.content, re.DOTALL).group(0))
    except:
        return [
            {"role":"logo","x":80,"y":80,"w":360,"h":180},
            {"role":"house","x":40,"y":280,"w":1000,"h":1300},
            {"role":"price","x":100,"y":1620,"w":880,"h":200},
            {"role":"contact","x":100,"y":1850,"w":880,"h":100}
        ]

# ====================== DRAW FRAME ======================
def draw_frame(t, imgs, boxes, price, location, features, caption):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), "#0a0a0a")
    draw = ImageDraw.Draw(canvas)

    # Dark gradient background
    for y in range(HEIGHT):
        alpha = y / HEIGHT
        draw.line([(0,y),(WIDTH,y)], fill=(int(10+20*alpha), int(5+15*alpha), int(20+30*alpha)))

    try:
        logo_resp = requests.get(LOGO_URL, stream=True, timeout=5)
        logo_resp.raise_for_status()
        logo = Image.open(logo_resp.raw).convert("RGBA")
    except Exception as e:
        st.warning(f"Logo load failed: {e}. Using blank.")
        logo = Image.new("RGBA", (1,1), (0,0,0,0))

    img_idx = int(t / (DURATION / len(imgs))) % len(imgs)  # Cycle through photos
    current_img = imgs[img_idx]

    for b in boxes:
        if b["role"] == "logo":
            resized_logo = logo.resize((b["w"], b["h"]))
            canvas.paste(resized_logo, (b["x"], b["y"]), resized_logo)
        if b["role"] == "house":
            zoom = 1.0 + 0.05 * math.sin(t * 2)  # Ken Burns zoom
            w2, h2 = int(b["w"]*zoom), int(b["h"]*zoom)
            prod = current_img.resize((w2, h2))
            canvas.paste(prod, (b["x"]+(b["w"]-w2)//2, b["y"]+(b["h"]-h2)//2), prod)
        if b["role"] == "price":
            bounce = 15 * math.sin(t * 3)
            draw.rounded_rectangle([b["x"], b["y"]+bounce, b["x"]+b["w"], b["y"]+b["h"]+bounce], radius=40, fill="#D4AF37")
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2+bounce), f"{price} in {location}", fill="white", anchor="mm", font_size=100, stroke_width=5, stroke_fill="black")
        if b["role"] == "contact":
            draw.text((b["x"]+b["w"]//2, b["y"]+b["h"]//2), features, fill="#D4AF37", anchor="mm", font_size=60)

    # Hook text fade-in
    if t < 2.5:
        draw.text((WIDTH//2, 300), caption.upper(), fill="white", anchor="mt", font_size=140, stroke_width=8, stroke_fill="black")

    return canvas

# ====================== UI ======================
uploaded_files = st.file_uploader("House Photos (Upload 1-5 for tour)", type=["png","jpg","jpeg"], accept_multiple_files=True)
price = st.text_input("Price", "KES 450,000")
location = st.text_input("Location", "Nairobi CBD")
features = st.text_input("Key Features", "3 Bed, Modern Kitchen, Pool")
contact = st.text_input("Contact Info", "Call 0710 338 377")

if st.button("Generate Reel", type="primary", use_container_width=True):
    if not uploaded_files:
        st.error("Upload at least 1 photo!")
    else:
        with st.spinner("AI Generating Your Reel..."):
            imgs = [Image.open(f).convert("RGBA") for f in uploaded_files]
            b64s = []
            for img in imgs:
                buf = io.BytesIO(); img.save(buf, format="PNG"); b64s.append(base64.b64encode(buf.getvalue()).decode())
            caption = get_caption(b64s[:3])  # Use first 3 for AI
            boxes = get_layout(price, location, features)

            # Generate silent video
            frames = [draw_frame(i/FPS, imgs, boxes, price, location, features, caption) for i in range(N_FRAMES)]
            silent_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            imageio.imwrite(silent_path, frames, fps=FPS, codec="libx264", pixelformat="yuv420p")

            # Add trending music (hotlink)
            audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            urllib.request.urlretrieve(MUSIC_URL, audio_temp)
            video = mp.VideoFileClip(silent_path)
            audio = mp.AudioFileClip(audio_temp).subclip(0, DURATION).volumex(0.7)
            final_video = video.set_audio(audio)
            final_path = silent_path.replace(".mp4", "_reel.mp4")
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", fps=FPS)

            # Cleanup
            os.unlink(silent_path); os.unlink(audio_temp)

        st.success(f"**AI Hook:** {caption}")
        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("Download Reel", f, f"RealEstate_{location.replace(' ', '_')}.mp4", "video/mp4")
        st.balloons()
