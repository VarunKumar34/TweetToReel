import streamlit as st
import yt_dlp
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip
import os

st.set_page_config(page_title="TweetReel Engine", page_icon="🎬")
st.title("🎬 Tweet-to-Reel Pro")

def create_tweet_card(display_name, username, pfp_url, tweet_text):
    """Creates a beautiful tweet card with rounded PFP and custom fonts."""
    # 1. Create a transparent canvas for the card
    card_w, card_h = 800, 350
    card = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    # Draw rounded background (Semi-transparent black)
    draw.rounded_rectangle([0, 0, card_w, card_h], radius=30, fill=(0, 0, 0, 180))
    
    # 2. Process Profile Picture (Make it circular)
    pfp_response = requests.get(pfp_url)
    pfp = Image.open(BytesIO(pfp_response.content)).convert("RGBA")
    pfp = ImageOps.fit(pfp, (100, 100), centering=(0.5, 0.5))
    
    mask = Image.new('L', (100, 100), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 100, 100), fill=255)
    pfp.putalpha(mask)
    
    card.paste(pfp, (40, 40), pfp)
    
    # 3. Add Text (Name, Username, Tweet)
    # Note: For production, upload a custom .ttf font to your repo
    draw.text((160, 45), display_name, fill="white", font_size=32)
    draw.text((160, 85), f"@{username}", fill="#8899A6", font_size=24)
    draw.text((40, 160), tweet_text[:140] + "...", fill="white", font_size=28)
    
    card.save("temp_card.png")
    return "temp_card.png"

# --- Main App Logic ---
url = st.text_input("Enter Tweet URL")

if st.button("Create Reel") and url:
    with st.spinner("Processing metadata..."):
        ydl_opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': 'input_vid.mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Create the card image
            card_path = create_tweet_card(
                info.get('uploader', 'User'),
                info.get('uploader_id', 'user'),
                info.get('thumbnail'), # yt-dlp often provides PFP as thumbnail
                info.get('description', '')
            )
            
            # Video Processing
            clip = VideoFileClip("input_vid.mp4").resize(height=1920)
            
            # Crop to 9:16
            w, h = clip.size
            clip = clip.crop(x_center=w/2, width=1080, height=1920)
            
            # Overlay Card
            overlay = (ImageClip(card_path)
                       .set_duration(clip.duration)
                       .set_position(("center", "center")))
            
            final = CompositeVideoClip([clip, overlay])
            final.write_videofile("final_reel.mp4", codec="libx264", audio_codec="aac")
            
            st.video("final_reel.mp4")
          
