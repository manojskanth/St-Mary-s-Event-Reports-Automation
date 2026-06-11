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
# 2. CORE INPUT PROCESSING DATA ZONE (PROPORTIONATE & RAW)
# =========================================================
with st.sidebar:
    st.header("Event Metadata Input")
    event_title = st.text_input("Event Title", placeholder="e.g., National Seminar on Indigenous Literature")
    event_date = st.date_input("Event Date")
    department = st.text_input("Organizing Department/Cell", value="Department of English and Languages")
    raw_inputs = st.text_area("Event Key Notes / Data Points", placeholder="Paste direct, raw facts, speakers, or student counts here...", height=250)

# Strict text builder without generic AI words, fluff, or asterisk bullet styling
def process_report_content(text_input, title_context):
    if not text_input.strip():
        return "No sufficient metadata provided to structure report narratives."
        
    # Split by lines and clean boundaries
    raw_lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    
    objectives_output = []
    outcomes_output = []
    
    for line in raw_lines:
        # Strip preexisting asterisk or dash characters if user pasted them
        clean_line = line.lstrip('*•- ').rstrip('.')
        
        # Guard against generic AI phrases or fluff
        if any(fluff in clean_line.lower() for fluff in ["here are", "objectives for", "tailored to", "foster an", "broader spectrum"]):
            continue
            
        # Keep generation length strictly proportionate to inputs provided
        objectives_output.append(f"To address the parameters of {clean_line.lower()}.")
        outcomes_output.append(f"Resulted in direct academic development regarding {clean_line.lower()}.")
        
    # Assemble raw text output blocks with zero conversational introductions
    structured_report = f"EVENT REPORT: {title_context.upper()}\n"
    structured_report += f"DATE: {event_date}\n"
    structured_report += f"ORGANIZING BODY: {department}\n\n"
    
    structured_report += "EVENT OBJECTIVES\n"
    if objectives_output:
        structured_report += "\n".join(objectives_output)
    else:
        structured_report += "Not specified."
        
    structured_report += "\n\nEVENT OUTCOMES\n"
    if outcomes_output:
        structured_report += "\n".join(outcomes_output)
    else:
        structured_report += "Not specified."
        
    return structured_report

# =========================================================
# 3. WORKSPACE DOCUMENT UPLOAD & STATUS TABS (EXACT LABELS)
# =========================================================
st.markdown('<div class="section-header">Institutional Verification Attachments</div>', unsafe_allow_html=True)

# Dictionary to hold the dropdown selection data across tabs to preserve original functionality
doc_status = {}

tab_brochure, tab_photos, tab_participants, tab_certificates, tab_winners = st.tabs([
    "Brochure/Circular",
    "Photos",
    "List of Participants with signatures",
    "Certificates Issued (with title and date)",
    "Winners’ details (If Competition)"
])

with tab_brochure:
    uploaded_brochure = st.file_uploader("Upload Brochure or Circular", accept_multiple_files=True, key="brochure")
    doc_status["Brochure/Circular"] = st.selectbox("Document Status:", ["Attached", "NA"], key="status_brochure")

with tab_photos:
    uploaded_photos = st.file_uploader("Upload Event Photos (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="photos")
    doc_status["Photos"] = st.selectbox("Document Status:", ["Attached", "NA"], key="status_photos")

with tab_participants:
    uploaded_participants = st.file_uploader("Upload Signed Participant Roster Lists", accept_multiple_files=True, key="participants")
    doc_status["List of Participants with signatures"] = st.selectbox("Document Status:", ["Attached", "NA"], key="status_participants")

with tab_certificates:
    uploaded_certificates = st.file_uploader("Upload Sample Certificates Issued", accept_multiple_files=True, key="certificates")
    doc_status["Certificates Issued (with title and date)"] = st.selectbox("Document Status:", ["Attached", "NA"], key="status_certificates")

with tab_winners:
    uploaded_winners = st.file_uploader("Upload Winner Breakdown Details", accept_multiple_files=True, key="winners")
    doc_status["Winners’ details (If Competition)"] = st.selectbox("Document Status:", ["Attached", "NA"], key="status_winners")

# =========================================================
# 4. COMPILING REPORT & ZIP ARCHIVE ENGINE
# =========================================================
st.markdown("---")
if st.button("Compile Event Document Package"):
    if not event_title:
        st.error("Action Blocked: Please specify a valid Event Title in the sidebar context manager.")
    else:
        # Build clean report without over-exaggeration or fluff words
        final_report_text = process_report_content(raw_inputs, event_title)
        
        # Append the document checklist selections to the foot of the generated text block
        final_report_text += "\n\n=========================================\n"
        final_report_text += "IQAC VERIFICATION DOCUMENT CHECKLIST STATUS\n"
        final_report_text += "=========================================\n"
        for doc_name, status in doc_status.items():
            final_report_text += f"{doc_name}: {status}\n"
            
        col_text, col_photos = st.columns(2)
        
        with col_text:
            st.subheader("Structured Document Preview")
            st.text_area("Text Output Window (Copy-Ready)", final_report_text, height=300)
            
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
                        photo_bytes = photo.read()
                        file_ext = photo.name.split(".")[-1]
                        archive_name = f"Photo_{idx+1}.{file_ext}"
                        zip_file.writestr(archive_name, photo_bytes)
                
                zip_buffer.seek(0)
                clean_folder_title = event_title.replace(" ", "_")
                
                # Download button for Photos Zip titled with Event Title
                st.download_button(
                    label="Download Photos Zip Folder",
                    data=zip_buffer,
                    file_name=f"{clean_folder_title}.zip",
                    mime="application/zip"
                )
            else:
                st.warning("No media assets found in the 'Photos' tab layout window.")
