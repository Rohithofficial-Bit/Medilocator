import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from geopy.geocoders import Nominatim
import google.generativeai as genai
import json

# Page config
st.set_page_config(
    page_title="MediLocator",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
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
</style>
""", unsafe_allow_html=True)

# Initialize API
GOOGLE_API_KEY = "AIzaSyCuBtANHlfl4SXGM6F5kifN6ronRedlzho"
genai.configure(api_key=GOOGLE_API_KEY)

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# Initialize session state
if 'location_set' not in st.session_state:
    st.session_state.location_set = False
if 'pincode' not in st.session_state:
    st.session_state.pincode = None
if 'location_data' not in st.session_state:
    st.session_state.location_data = None

# Header
st.markdown("# 💊 MediLocator")
st.markdown("### Find medicine availability at nearby pharmacies in real-time")
st.markdown("---")

# Location Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📍 Enter Your Pincode")
    
    if not st.session_state.location_set:
        st.info("🔢 Enter your 6-digit pincode to get started")
        
        pincode_input = st.text_input(
            "Pincode *",
            placeholder="e.g., 641001, 560001, 110001...",
            max_chars=6,
            help="Enter 6-digit Indian pincode",
            key="pincode_entry"
        )
        
        if st.button("📍 Set Location", key="set_pincode", type="primary"):
            if pincode_input and len(pincode_input) == 6 and pincode_input.isdigit():
                with st.spinner("🔍 Getting location details..."):
                    try:
                        # Use geocoder to get location from pincode
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
                            st.success(f"✅ Location set: {location.address}")
                            st.rerun()
                        else:
                            st.error("❌ Invalid pincode or location not found. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            elif not pincode_input:
                st.warning("⚠️ Please enter a pincode")
            elif len(pincode_input) != 6:
                st.warning("⚠️ Pincode must be 6 digits")
            else:
                st.warning("⚠️ Pincode must contain only numbers")
    else:
        # Show current location
        st.markdown(f'<div class="location-badge">📌 Pincode: {st.session_state.pincode}</div>', unsafe_allow_html=True)
        st.markdown(f"**Location:** {st.session_state.location_data['address']}")
        
        if st.button("🔄 Change Pincode"):
            st.session_state.location_set = False
            st.session_state.pincode = None
            st.session_state.location_data = None
            st.rerun()

with col2:
    st.markdown("## 🎯 Quick Stats")
    if st.session_state.location_set:
        st.markdown(f'<div class="metric-card"><h3>📮 Pincode</h3><p style="font-size:2rem;color:#667eea;font-weight:bold;">{st.session_state.pincode}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="metric-card"><h3>🏪 Pharmacies</h3><p style="font-size:2rem;color:#667eea;font-weight:bold;">Ready</p></div>', unsafe_allow_html=True)

st.markdown("---")

# Medicine Search Section
st.markdown("## 💊 Search Medicine")

medicine = st.text_input(
    "Enter medicine name",
    placeholder="e.g., Paracetamol, Dolo 650, Amoxicillin...",
    help="Type the medicine name you're looking for"
)

search_button = st.button("🔍 Find Pharmacies", type="primary")

if search_button and medicine and st.session_state.location_set:
    with st.spinner("🤖 AI is searching for pharmacies and checking availability..."):
        
        # Create AI prompt to find pharmacies
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

Return ONLY a valid JSON array with this structure:
[
  {{
    "name": "Pharmacy Name",
    "address": "Full address with pincode",
    "lat": 11.0172,
    "lon": 76.9578,
    "in_stock": true,
    "contact": "+91-XXXXXXXXXX",
    "distance_km": 1.2,
    "hours": "8:00 AM - 10:00 PM"
  }}
]

Make the data realistic and varied. Some pharmacies should have stock, others shouldn't. Include the pincode {pincode} in addresses.
""")
        
        # Get pharmacy data from AI
        chain = pharmacy_prompt | model
        response = chain.invoke({
            "medicine": medicine,
            "pincode": st.session_state.pincode,
            "lat": st.session_state.location_data['lat'],
            "lon": st.session_state.location_data['lon'],
            "location_name": st.session_state.location_data['address']
        })
        
        # Parse AI response
        try:
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            pharmacies = json.loads(content.strip())
            
            # Get medicine information
            medicine_prompt = ChatPromptTemplate.from_template("""
Provide a brief, helpful summary about the medicine "{medicine}":
- Common uses (2-3 points)
- Typical dosage form (tablet/syrup/injection)
- Important note (if any)

Keep it concise, under 100 words, and patient-friendly.
""")
            
            med_chain = medicine_prompt | model
            med_info = med_chain.invoke({"medicine": medicine}).content
            
            # Display medicine info
            st.markdown(f"""
<div class="medicine-info">
    <h3>💊 About {medicine}</h3>
    <p>{med_info}</p>
</div>
""", unsafe_allow_html=True)
            
            # Separate available and unavailable pharmacies
            available = [p for p in pharmacies if p.get('in_stock', False)]
            unavailable = [p for p in pharmacies if not p.get('in_stock', False)]
            
            # Display results
            if available:
                st.markdown(f"## ✅ Found at {len(available)} Pharmacies in {st.session_state.pincode}")
                
                for pharmacy in available:
                    address = pharmacy.get('address', 'Address not available')
                    st.markdown(f"""
<div class="pharmacy-card">
    <h3>🏪 {pharmacy['name']}</h3>
    <p><strong>📍 Address:</strong> {address}</p>
    <p><strong>📏 Distance:</strong> {pharmacy['distance_km']} km away</p>
    <p><strong>📞 Contact:</strong> {pharmacy['contact']}</p>
    <p><strong>🕐 Hours:</strong> {pharmacy['hours']}</p>
    <p><strong>✅ Status:</strong> <span style="color:#4CAF50;font-weight:bold;">IN STOCK</span></p>
</div>
""", unsafe_allow_html=True)
            
            if unavailable:
                with st.expander(f"❌ Not available at {len(unavailable)} other pharmacies"):
                    for pharmacy in unavailable:
                        address = pharmacy.get('address', 'Address not available')
                        st.markdown(f"""
<div class="pharmacy-card" style="opacity:0.7;">
    <h4>🏪 {pharmacy['name']}</h4>
    <p><strong>📍 Address:</strong> {address}</p>
    <p><strong>📏 Distance:</strong> {pharmacy['distance_km']} km away</p>
    <p><strong>❌ Status:</strong> <span style="color:#f44336;font-weight:bold;">OUT OF STOCK</span></p>
</div>
""", unsafe_allow_html=True)
            
            if not available:
                st.warning(f"⚠️ {medicine} is currently not available at pharmacies in pincode {st.session_state.pincode}. Try calling them directly or check alternative medicines.")
                
        except json.JSONDecodeError:
            st.error("❌ Could not parse pharmacy data. Please try again.")
            st.text("AI Response:")
            st.text(response.content)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

elif search_button and not st.session_state.location_set:
    st.warning("⚠️ Please enter your pincode first!")
elif search_button and not medicine:
    st.warning("⚠️ Please enter a medicine name!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>💡 <strong>Tip:</strong> Call ahead to confirm availability before visiting</p>
    <p style='font-size:0.9rem;'>Made with ❤️ using Gemini AI | Data is generated for demonstration purposes</p>
</div>
""", unsafe_allow_html=True)