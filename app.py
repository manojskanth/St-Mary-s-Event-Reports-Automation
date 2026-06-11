import streamlit as st
import io
import zipfile
import re

# =========================================================
# 1. PAGE INITIALIZATION & CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="St. Mary's Institutional Event Report Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS styling parameters
st.markdown("""
    <style>
    .main-title { font-size:26px !important; font-weight: bold; color: #1F4E78; margin-bottom: 5px; }
    .sub-title { font-size:14px !important; font-style: italic; color: #5A5A5A; margin-bottom: 25px; }
    .section-header { font-size:18px !important; font-weight: bold; color: #1F4E78; margin-top: 20px; }
    div.stButton > button:first-child { background-color: #1F4E78; color: white; border-radius: 4px; }
    div.stDownloadButton > button:first-child { background-color: #2E7D32; color: white; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">St. Mary\'s College</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Internal Quality Assurance Cell (IQAC) — Automated Event Report Engine</div>', unsafe_allow_html=True)

# =========================================================
# 2. CORE INPUT PROCESSING DATA ZONE
# =========================================================
with st.sidebar:
    st.header("Event Metadata Input")
    event_title = st.text_input("Event Title", placeholder="e.g., National Seminar on Indigenous Literature")
    event_date = st.date_input("Event Date")
    department = st.text_input("Organizing Department/Cell", value="Department of English and Languages")
    raw_inputs = st.text_area("Event Key Notes / Data Points", placeholder="Paste direct, raw facts, speakers, or student counts here...", height=250)

# Clean, bulletless clean extraction processor rule
def process_report_content(text_input, title_context):
    if not text_input.strip():
        return "No sufficient metadata provided to structure report narratives."
        
    # Split sentences cleanly to isolate core input points
    lines = [line.strip() for line in re.split(r'[\n•\-\*]+', text_input) if line.strip()]
    
    objectives_output = []
    outcomes_output = []
    
    for line in lines:
        # Prevent generic AI structural fluff phrases
        if any(fluff in line.lower() for fluff in ["here are", "objectives for", "tailored to", "foster an", "broader spectrum"]):
            continue
        # Clean structural constraints to match user input proportion exactly
        clean_fact = line.rstrip('.')
        objectives_output.append(f"Advance scholarly awareness regarding {clean_fact.lower()}.")
        outcomes_output.append(f"Documented direct academic outcomes matching the presentation of {clean_fact.lower()}.")
        
    # Build strict text blocks with no conversational filler or asterisk bullets
    structured_report = f"EVENT REPORT: {title_context.upper()}\n"
    structured_report += f"DATE: {event_date}\n"
    structured_report += f"ORGANIZING BODY: {department}\n\n"
    
    structured_report += "EVENT OBJECTIVES\n"
    structured_report += "\n".join(objectives_output) if objectives_output else "Core data points not specified."
    
    structured_report += "\n\nEVENT OUTCOMES\n"
    structured_report += "\n".join(outcomes_output) if outcomes_output else "Core data points not specified."
    
    return structured_report

# =========================================================
# 3. WORKSPACE DOCUMENT UPLOAD LAYER (EXACT LABELS)
# =========================================================
st.markdown('<div class="section-header">Institutional Verification Attachments</div>', unsafe_allow_html=True)

tab_brochure, tab_photos, tab_participants, tab_certificates, tab_winners = st.tabs([
    "Brochure/Circular",
    "Photos",
    "List of Participants with signatures",
    "Certificates Issued (with title and date)",
    "Winners’ details (If Competition)"
])

with tab_brochure:
    uploaded_brochure = st.file_uploader("Upload Brochure or Circular (PDF/Images)", accept_multiple_files=True, key="brochure")

with tab_photos:
    uploaded_photos = st.file_uploader("Upload Event Photos (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="photos")

with tab_participants:
    uploaded_participants = st.file_uploader("Upload Signed Participant Roster Lists (PDF/Scans)", accept_multiple_files=True, key="participants")

with tab_certificates:
    uploaded_certificates = st.file_uploader("Upload Sample Certificates Issued (PDF/Images)", accept_multiple_files=True, key="certificates")

with tab_winners:
    is_competition = st.checkbox("Is this event an institutional competition?")
    if is_competition:
        uploaded_winners = st.file_uploader("Upload Winner Breakdown Details Spreadsheet/PDF", accept_multiple_files=True, key="winners")
    else:
        st.info("Uncheck if this was a seminar, workshop, or regular guest lecture session.")

# =========================================================
# 4. COMPILING REPORT & ZIP ARCHIVE ENGINE
# =========================================================
st.markdown("---")
if st.button("Compile Event Document Package"):
    if not event_title:
        st.error("Action Blocked: Please specify a valid Event Title in the sidebar context manager.")
    else:
        # Process clean prose narratives
        final_report_text = process_report_content(raw_inputs, event_title)
        
        col_text, col_photos = st.columns(2)
        
        with col_text:
            st.subheader("Structured Document Preview")
            st.text_area("Text Output Window (Copy-Ready)", final_report_text, height=300)
            
            # Download button for Report Text
            st.download_button(
                label="Download Official Event Report (.txt)",
                data=final_report_text,
                file_name=f"Report_{event_title.replace(' ', '_')}.txt",
                mime="text/plain"
            )
            
        with col_photos:
            st.subheader("Media Distribution Package")
            if uploaded_photos:
                st.success(f"Detected {len(uploaded_photos)} images uploaded in verification repository.")
                
                # --- MEMORY ZIP COMPRESSION ENGINE ---
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, photo in enumerate(uploaded_photos):
                        # Read binary data bytes stream from input tab memory array
                        photo_bytes = photo.read()
                        # Clean file extension tracking strings
                        file_ext = photo.name.split(".")[-1]
                        # Use clean indexing naming for the files inside zip archive drawer
                        archive_name = f"Photo_{idx+1}.{file_ext}"
                        zip_file.writestr(archive_name, photo_bytes)
                
                zip_buffer.seek(0)
                clean_folder_title = event_title.replace(" ", "_")
                
                # Download button for Photos Zip
                st.download_button(
                    label="Download Photos Zip Folder",
                    data=zip_buffer,
                    file_name=f"{clean_folder_title}.zip",
                    mime="application/zip"
                )
            else:
                st.warning("No media assets found in the 'Photos' tab layout window.")
