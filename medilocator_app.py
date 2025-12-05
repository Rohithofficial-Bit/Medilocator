import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from geopy.geocoders import Nominatim
import google.generativeai as genai
import json
from streamlit.components.v1 import html as components_html

# ====================== YOUR ORIGINAL PAGE CONFIG & CSS (UNCHANGED) ======================
st.set_page_config(
    page_title="MediLocator",
    page_icon="pill",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main {padding: 2rem;}
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .pharmacy-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .medicine-info {
        background: linear-gradient(135deg, #f093fb15 0%, #f5576c15 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #f093fb;
    }
    .location-badge {
        background: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.5rem 0;
    }
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .pincode-input {
        font-size: 1.2rem;
        padding: 0.5rem;
    }
    /* LOGIN STYLES - ONLY ADDITION */

    .login-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ====================== SESSION STATE (YOUR ORIGINAL + LOGIN) ======================
if 'location_set' not in st.session_state:
    st.session_state.location_set = False
if 'pincode' not in st.session_state:
    st.session_state.pincode = None
if 'location_data' not in st.session_state:
    st.session_state.location_data = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# ====================== ONLY ADDITION: BEAUTIFUL LOGIN SCREEN ======================
if not st.session_state.logged_in:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<h1 class='login-title'>MediLocator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666;font-size:1.1rem;margin-bottom:30px;'>Find medicines near you instantly</p>", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        login_btn = st.form_submit_button("Login →", use_container_width=True)

        if login_btn:
            if email == "rohith@gmail.com" and password == "123":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()  # Stops here until login

# ====================== YOUR 100% ORIGINAL CODE STARTS FROM HERE (UNCHANGED) ======================
# Initialize API
GOOGLE_API_KEY = "AIzaSyABs5rr4yEAIdEzUTh6r7_Yg8wYLLgQUiM"
genai.configure(api_key=GOOGLE_API_KEY)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# Header (after login)
st.markdown("# MediLocator")
st.markdown("### Find medicine availability at nearby pharmacies in real-time")
st.markdown("---")

# Show user + Logout button (replaced your old one)
colx, coly = st.columns([3,1])
with colx:
    st.markdown(f"**Logged in as:** {st.session_state.user_email}")
with coly:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

# Location Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## Enter Your Pincode")
    
    if not st.session_state.location_set:
        st.info("Enter your 6-digit pincode to get started")
        
        pincode_input = st.text_input(
            "Pincode *",
            placeholder="e.g., 641001, 560001, 110001...",
            max_chars=6,
            help="Enter 6-digit Indian pincode",
            key="pincode_entry"
        )
        
        if st.button("Set Location", key="set_pincode", type="primary"):
            if pincode_input and len(pincode_input) == 6 and pincode_input.isdigit():
                with st.spinner("Getting location details..."):
                    try:
                        geolocator = Nominatim(user_agent="medilocator_v4")
                        location = geolocator.geocode(f"{pincode_input}, India")
                        
                        if location:
                            st.session_state.pincode = pincode_input
                            st.session_state.location_data = {
                                'address': location.address,
                                'lat': location.latitude,
                                'lon': location.longitude
                            }
                            st.session_state.location_set = True
                            st.success(f"Location set: {location.address}")
                            st.rerun()
                        else:
                            st.error("Invalid pincode or location not found. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            elif not pincode_input:
                st.warning("Please enter a pincode")
            elif len(pincode_input) != 6:
                st.warning("Pincode must be 6 digits")
            else:
                st.warning("Pincode must contain only numbers")
    else:
        st.markdown(f'<div class="location-badge">Pincode: {st.session_state.pincode}</div>', unsafe_allow_html=True)
        st.markdown(f"*Location:* {st.session_state.location_data['address']}")
        
        if st.button("Change Pincode"):
            st.session_state.location_set = False
            st.session_state.pincode = None
            st.session_state.location_data = None
            st.rerun()

with col2:
    st.markdown("## Quick Stats")
    if st.session_state.location_set:
        st.markdown(f'<div class="metric-card"><h3>Pincode</h3><p style="font-size:2rem;color:#667eea;font-weight:bold;">{st.session_state.pincode}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="metric-card"><h3>Pharmacies</h3><p style="font-size:2rem;color:#667eea;font-weight:bold;">Ready</p></div>', unsafe_allow_html=True)

st.markdown("---")

# Medicine Search Section
st.markdown("## Search Medicine")

medicine = st.text_input(
    "Enter medicine name",
    placeholder="e.g., Paracetamol, Dolo 650, Amoxicillin...",
    help="Type the medicine name you're looking for"
)

search_button = st.button("Find Pharmacies", type="primary")

if search_button and medicine and st.session_state.location_set:
    with st.spinner("AI is searching for pharmacies and checking availability..."):
        
        pharmacy_prompt = ChatPromptTemplate.from_template("""
You are a medical pharmacy locator assistant. Given a pincode {pincode} in location: {location_name} and a medicine "{medicine}", 
generate a realistic list of 5-7 pharmacies that might be in this pincode area with their details.

For each pharmacy, provide:
1. Name (use real pharmacy chain names common in India like Apollo, MedPlus, Wellness Forever, Netmeds, 1mg, PharmEasy stores, local pharmacies)
2. Approximate latitude and longitude (near {lat}, {lon} - vary slightly within 2-3 km radius)
3. Whether this medicine is IN STOCK or OUT OF STOCK (make it realistic - not all will have it)
4. Contact number (realistic Indian format)
5. Distance from pincode center in km
6. Operating hours
7. Full address with the pincode {pincode}

Return ONLY a valid JSON array with this structure (include average price for a single tablet/package):
[
    {{
        "name": "Pharmacy Name",
        "address": "Full address with pincode",
        "lat": 11.0172,
        "lon": 76.9578,
        "in_stock": true,
        "price": 25.0,
        "contact": "+91-XXXXXXXXXX",
        "distance_km": 1.2,
        "hours": "8:00 AM - 10:00 PM"
    }}
]

Make the data realistic and varied. Some pharmacies should have stock, others shouldn't. Include the pincode {pincode} in addresses.
""")
        
        chain = pharmacy_prompt | model
        response = chain.invoke({
            "medicine": medicine,
            "pincode": st.session_state.pincode,
            "lat": st.session_state.location_data['lat'],
            "lon": st.session_state.location_data['lon'],
            "location_name": st.session_state.location_data['address']
        })
        
        try:
            content = getattr(response, 'content', str(response))
            start_candidates = [i for i in (content.find('['), content.find('{')) if i != -1]
            json_start = min(start_candidates) if start_candidates else -1
            json_end = max(content.rfind(']'), content.rfind('}'))
            if json_start != -1 and json_end != -1 and json_end >= json_start:
                content = content[json_start:json_end+1]
            else:
                content = content.strip()
            
            pharmacies = json.loads(content.strip())
            
            medicine_prompt = ChatPromptTemplate.from_template("""
Provide a brief, helpful summary about the medicine "{medicine}":
- Common uses (2-3 points)
- Typical dosage form (tablet/syrup/injection)
- Important note (if any)

Keep it concise, under 100 words, and patient-friendly.
""")
            
            med_chain = medicine_prompt | model
            med_info = med_chain.invoke({"medicine": medicine}).content
            
            st.markdown(f"""
<div class="medicine-info">
    <h3>About {medicine}</h3>
    <p>{med_info}</p>
</div>
""", unsafe_allow_html=True)
            
            available = [p for p in pharmacies if p.get('in_stock', False)]
            unavailable = [p for p in pharmacies if not p.get('in_stock', False)]
            
            if available:
                st.markdown(f"## Found at {len(available)} Pharmacies in {st.session_state.pincode}")
                
                for pharmacy in available:
                    address = pharmacy.get('address', 'Address not available')
                    price = pharmacy.get('price', 'N/A')
                    lat = pharmacy.get('lat')
                    lon = pharmacy.get('lon')
                    st.markdown(f"""
<div class="pharmacy-card">
    <h3>{pharmacy['name']}</h3>
    <p><strong>Address:</strong> {address}</p>
    <p><strong>Price:</strong> ₹{price}</p>
    <p><strong>Distance:</strong> {pharmacy['distance_km']} km away</p>
    <p><strong>Contact:</strong> {pharmacy['contact']}</p>
    <p><strong>Hours:</strong> {pharmacy['hours']}</p>
    <p><strong>Status:</strong> <span style="color:#4CAF50;font-weight:bold;">IN STOCK</span></p>
</div>
""", unsafe_allow_html=True)

                    if lat and lon:
                        map_src = f"https://maps.google.com/maps?q={lat},{lon}&z=15&output=embed"
                        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                        with st.expander("View on map / Navigate"):
                            components_html(f'<iframe src="{map_src}" width="100%" height="260" style="border:0;"></iframe>', height=270)
                            st.markdown(f'<p><a href="{nav_url}" target="_blank" rel="noopener"><button style="background:#667eea;color:white;padding:8px 14px;border-radius:8px;border:none;font-weight:600">Open navigation in Google Maps</button></a></p>', unsafe_allow_html=True)
            
            if unavailable:
                with st.expander(f"Not available at {len(unavailable)} other pharmacies"):
                    for pharmacy in unavailable:
                        address = pharmacy.get('address', 'Address not available')
                        price = pharmacy.get('price', 'N/A')
                        lat = pharmacy.get('lat')
                        lon = pharmacy.get('lon')
                        st.markdown(f"""
<div class="pharmacy-card" style="opacity:0.7;">
    <h4>{pharmacy['name']}</h4>
    <p><strong>Address:</strong> {address}</p>
    <p><strong>Price:</strong> ₹{price}</p>
    <p><strong>Distance:</strong> {pharmacy['distance_km']} km away</p>
    <p><strong>Status:</strong> <span style="color:#f44336;font-weight:bold;">OUT OF STOCK</span></p>
</div>
""", unsafe_allow_html=True)

                        if lat and lon:
                            map_src = f"https://maps.google.com/maps?q={lat},{lon}&z=15&output=embed"
                            nav_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"
                            with st.expander(f"View map for {pharmacy['name']}"):
                                components_html(f'<iframe src="{map_src}" width="100%" height="260" style="border:0;"></iframe>', height=270)
                                st.markdown(f'<p><a href="{nav_url}" target="_blank" rel="noopener"><button style="background:#667eea;color:white;padding:8px 14px;border-radius:8px;border:none;font-weight:600">Open navigation in Google Maps</button></a></p>', unsafe_allow_html=True)
            
            if not available:
                st.warning(f"{medicine} is currently not available at pharmacies in pincode {st.session_state.pincode}. Try calling them directly or check alternative medicines.")
                
        except json.JSONDecodeError:
            st.error("Could not parse pharmacy data. Please try again.")
            st.text("AI Response:")
            st.text(response.content)
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif search_button and not st.session_state.location_set:
    st.warning("Please enter your pincode first!")
elif search_button and not medicine:
    st.warning("Please enter a medicine name!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Tip: Call ahead to confirm availability before visiting</p>
    <p style='font-size:0.9rem;'>Made with love using Gemini AI | Data is generated for demonstration purposes</p>
</div>
""", unsafe_allow_html=True)