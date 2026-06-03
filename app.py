import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
import google.generativeai as genai
import datetime
import io
import re

# --- 1. CORE CONFIGURATION ---
DEPARTMENTS = [
    "English & Languages", 
    "Social Sciences & Humanities", 
    "Sciences", 
    "Management", 
    "Commerce",
    "IQAC",
    "Research & Innovation"
]

ACADEMIC_YEARS = [
    "2024-25", "2025-26", "2026-27", "2027-28", "2028-29", "2029-30"
]

# --- 2. AI ENGINE (Refined Rules & Expanded Social Media Payload) ---
def generate_ai_content(section_name, notes, dept_name="", title_text="", style="formal"):
    model_name = 'gemini-2.5-flash-lite' 
    
    if style == "social":
        rules = (
            "Write a detailed narrative event summary post based on the notes. "
            "Include an engaging hook, a comprehensive body breakdown paragraph, and finish "
            "by dynamically generating exactly 6 to 8 highly relevant trending hashtags based on the "
            f"Department: {dept_name} and Event: {title_text}. Do not use intro fluff or conversational tags."
        )
    elif section_name in ["Objectives", "Learning Outcomes"]:
        rules = "Exactly 2 bullet points, max 2 lines each. Strict academic tone."
    else: # IQAC Narrative
        rules = "Formal academic summary. STRICT LIMIT: Max 150 words. No intro fluff."

    prompt = f"Task: Write '{section_name}' for St. Mary's College. Notes: {notes}. Rules: {rules}"
    
    # Automatically cleans up any accidental copy-paste trailing spaces from secrets
    api_key_clean = st.secrets["GEMINI_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=api_key_clean)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    
    return re.sub(r'[^\x00-\x7F]+', ' ', response.text).replace("**", "").strip()

# --- 3. UI LAYOUT MATRIX SETUP ---
st.set_page_config(page_title="St. Mary's Event Report Portal", layout="wide")

# Logo Alignment: Reads local logo.png natively from the root folder
left_pad, center_logo, right_pad = st.columns([1.8, 1.0, 1.8])
with center_logo:
    try:
        with open("logo.png", "rb") as image_file:
            st.image(image_file.read(), use_container_width=True)
    except Exception:
        st.markdown("<h3 style='text-align: center; color: #aaa;'>🏫 St. Mary's College</h3>", unsafe_allow_html=True)

st.markdown("<h1 style='font-size: 2.5em; text-align: center; margin-bottom: 0px;'>Event Report Generator Desk</h1>", unsafe_allow_html=True)
st.markdown("<hr style='margin:15px 0px;' />", unsafe_allow_html=True)

# Initialize Session States
if 'iqac_file' not in st.session_state:
    st.session_state.iqac_file = None
if 'sm_file' not in st.session_state:
    st.session_state.sm_file = None

with st.form("main_form"):
    st.subheader("1. Profile & Metadata")
    c1, c2 = st.columns(2)
    with c1:
        event_title = st.text_input("Event Title", placeholder="Enter official name of the event...")
        event_date = st.date_input("Event Date", datetime.date.today())
        form_dept = st.selectbox("Select Department / Cell", ["-- Select Department --"] + DEPARTMENTS)
    with c2:
        organizer = st.text_input("Event In-charge / Faculty Name", placeholder="Enter organizer's name...")
        participants = st.number_input("No. of Participants", min_value=0, step=1)
        academic_year = st.selectbox("Select Academic Year", ["-- Select Academic Year --"] + ACADEMIC_YEARS)

    raw_notes = st.text_area("Paste Event Notes / Narrative Data here", height=150)

    st.subheader("2. Supporting Documents Status")
    
    doc_options = ["-- Select Status --", "Attached", "NA"]
    
    d_cols = st.columns(5)
    att_a = d_cols[0].selectbox("Brochure", doc_options, key="status_brochure")
    att_b = d_cols[1].selectbox("Photos", doc_options, key="status_photos")
    att_c = d_cols[2].selectbox("List", doc_options, key="status_list")
    att_d = d_cols[3].selectbox("Certificates", doc_options, key="status_cert")
    att_e = d_cols[4].selectbox("Winners", doc_options, key="status_winners")

    st.subheader("3. Document Asset Uploads")
    up1, up2 = st.columns(2)
    with up1:
        brochure_file = st.file_uploader("Upload Brochure", type=['jpg','png','jpeg'])
        attendance_file = st.file_uploader("Upload Attendance/List", type=['jpg','png','jpeg'])
    with up2:
        event_photos = st.file_uploader("Photos (Up to 6 Assets)", type=['jpg','png','jpeg'], accept_multiple_files=True)

    submit = st.form_submit_button("🚀 Generate Both Compiled Reports", use_container_width=True)

# --- 4. DATA COMPILATION ENGINE LOGIC ---
if submit:
    # STRICT DOCUMENT VALIDATION LAYER: Checks if any drop down is left on placeholder
    unselected_docs = []
    if att_a == "-- Select Status --": unselected_docs.append("Brochure")
    if att_b == "-- Select Status --": unselected_docs.append("Photos")
    if att_c == "-- Select Status --": unselected_docs.append("Participant List")
    if att_d == "-- Select Status --": unselected_docs.append("Certificates")
    if att_e == "-- Select Status --": unselected_docs.append("Winners Details")

    if form_dept == "-- Select Department --":
        st.error("Form Validation Error: Please select an explicit Department/Cell.")
    elif academic_year == "-- Select Academic Year --":
        st.error("Form Validation Error: Please select the explicit Academic Year.")
    elif not event_title.strip():
        st.error("Form Validation Error: Event Title cannot be blank.")
    elif not raw_notes.strip():
        st.error("Form Validation Error: Narrative context notes are required!")
    elif unselected_docs:
        # Halts processing immediately and reports exactly which items are incomplete
        st.error(f"Form Validation Error: Please select either 'Attached' or 'NA' for the following items: {', '.join(unselected_docs)}")
    else:
        try:
            with st.spinner("AI Processing System executing template compilation layers..."):
                iqac_rep = generate_ai_content("Narrative", raw_notes, style="formal")
                obj = generate_ai_content("Objectives", raw_notes, style="formal")
                out = generate_ai_content("Learning Outcomes", raw_notes, style="formal")
                sm_rep = generate_ai_content("Social Media", raw_notes, dept_name=form_dept, title_text=event_title.strip(), style="social")

            def create_doc(template_path, is_iqac=True):
                doc = DocxTemplate(template_path)
                
                if form_dept in ["IQAC", "Research & Innovation"]:
                    dynamic_dept_header = form_dept
                else:
                    dynamic_dept_header = f"Department of {form_dept}"
                
                ctx = {
                    'event_title': str(event_title).strip(),
                    'event_date': event_date.strftime("%d-%m-%Y"),
                    'academic_year': str(academic_year),
                    'organizer': str(organizer).strip(),
                    'dept': str(form_dept), 
                    'dept_header': dynamic_dept_header,  
                    'participants': str(participants),
                    'report_body': str(iqac_rep if is_iqac else sm_rep),
                    'objectives': str(obj if is_iqac else ""),
                    'outcomes': str(out if is_iqac else ""),
                    
                    'attach_a': str(att_a), 
                    'attach_b': str(att_b), 
                    'attach_c': str(att_c),
                    'attach_d': str(att_d), 
                    'attach_e': str(att_e),
                    
                    'brochure_img': "", 'attendance_img': "",
                    'image_1': "", 'image_2': "", 'image_3': "",
                    'image_4': "", 'image_5': "", 'image_6': ""
                }
                
                if brochure_file: 
                    ctx['brochure_img'] = InlineImage(doc, io.BytesIO(brochure_file.getvalue()), width=Inches(4.5))
                if attendance_file: 
                    ctx['attendance_img'] = InlineImage(doc, io.BytesIO(attendance_file.getvalue()), width=Inches(4.5))
                if event_photos:
                    for i, p in enumerate(event_photos[:6]): 
                        ctx[f'image_{i+1}'] = InlineImage(doc, io.BytesIO(p.getvalue()), width=Inches(3.2))
                
                doc.render(ctx)
                buf = io.BytesIO()
                doc.save(buf)
                buf.seek(0)
                return buf

            st.session_state.iqac_file = create_doc("Sample_Event_Report_Template.docx", is_iqac=True)
            st.session_state.sm_file = create_doc("Social_Media_Report_Template.docx", is_iqac=False)
            st.success("✅ Both reports generated seamlessly and packaged successfully!")

        except Exception as e:
            st.error(f"System Operational Exception: {e}")

if st.session_state.iqac_file and st.session_state.sm_file:
    dl_col1, dl_col2 = st.columns(2)
    dl_col1.download_button(
        label="⬇️ Download IQAC Word Report Doc",
        data=st.session_state.iqac_file,
        file_name=f"IQAC_Report_{event_title.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    dl_col2.download_button(
        label="⬇️ Download Social Media Compilation Doc",
        data=st.session_state.sm_file,
        file_name=f"Social_Media_Brief_{event_title.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("<br><hr/><p style='text-align: center; font-size: 1.05em; font-weight: bold; color: #555;'>Developed by IQAC @ St. Mary's</p>", unsafe_allow_html=True)
