import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
import google.generativeai as genai
import datetime
import io
import re
import zipfile
import csv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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

# Comprehensive multi-format extension matrix allowance
ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png']
LOG_FILE_PATH = "report_generation_log.csv"
TARGET_EMAIL = "manojkanth@stmaryscollege.in"

# --- 2. AUTOMATED BACKGROUND UTILITIES (LOGGING & EMAIL) ---
def write_audit_log(user_name, department, title_text):
    """Logs the session activity dynamically to a clear path tracking file."""
    file_exists = os.path.isfile(LOG_FILE_PATH)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Faculty In-Charge", "Department/Cell", "Event Title"])
        writer.writerow([timestamp, user_name, department, title_text])

def email_compiled_reports(event_title, dept_name, iqac_bytes, sm_bytes):
    """Dispatches the finished document attachments straight to your inbox."""
    if "EMAIL_HOST_USER" not in st.secrets or "EMAIL_HOST_PASSWORD" not in st.secrets:
        st.warning("⚠️ Email configuration missing from st.secrets. Reports saved locally only.")
        return False
        
    try:
        sender_email = st.secrets["EMAIL_HOST_USER"]
        sender_password = st.secrets["EMAIL_HOST_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = TARGET_EMAIL
        msg['Subject'] = f"Official Event Report Compiled: {event_title} [{dept_name}]"
        
        body = f"Please find attached the compiled event report documents generated on {datetime.date.today().strftime('%d-%m-%Y')}."
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach IQAC Word Report
        part_iqac = MIMEBase('application', 'octet-stream')
        part_iqac.set_payload(iqac_bytes.getvalue())
        encoders.encode_base64(part_iqac)
        part_iqac.add_header('Content-Disposition', f'attachment; filename="IQAC_Report_{event_title.replace(" ", "_")}.docx"')
        msg.attach(part_iqac)
        
        # Attach Social Media Media Package
        part_sm = MIMEBase('application', 'octet-stream')
        part_sm.set_payload(sm_bytes.getvalue())
        encoders.encode_base64(part_sm)
        part_sm.add_header('Content-Disposition', f'attachment; filename="Social_Media_Brief_{event_title.replace(" ", "_")}.docx"')
        msg.attach(part_sm)
        
        # Secure TLS channel deployment
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, TARGET_EMAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Delivery Interruption: {e}")
        return False

# --- 3. AI ENGINE (Proportionate, Fluff-Free & Bulletless Prose) ---
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
        rules = (
            "Write exactly 2 lines. Do not use asterisks, hyphens, bullet points, or numbering. "
            "Write as plain, direct text blocks. Avoid generic buzzwords like 'to foster', 'to highlight', or 'tailored to'. "
            "Keep the length of the content strictly proportionate to the volume of input facts provided without exaggerating details."
        )
    else: # IQAC Narrative
        rules = (
            "Formal academic summary. STRICT LIMIT: Max 150 words. No intro fluff or placeholder text. "
            "Keep content strictly proportionate to inputs provided without exaggerating or hallucinating additional events."
        )

    prompt = f"Task: Write '{section_name}' for St. Mary's College. Notes: {notes}. Rules: {rules}"
    
    api_key_clean = st.secrets["GEMINI_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=api_key_clean)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    
    cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', response.text).replace("**", "").replace("*", "").strip()
    return cleaned_text

# --- 4. UI LAYOUT MATRIX SETUP ---
st.set_page_config(page_title="St. Mary's Event Report Generator", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #1F4E78; color: white; border-radius: 4px; }
    div.stDownloadButton > button:first-child { background-color: #2E7D32; color: white; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

left_pad, center_logo, right_pad = st.columns([1.8, 3.0, 1.8])
with center_logo:
    try:
        with open("logo.png", "rb") as image_file:
            st.image(image_file.read(), use_container_width=True)
    except Exception:
        st.markdown("<h3 style='text-align: center; color: #1F4E78;'>🏫 St. Mary's College</h3>", unsafe_allow_html=True)

st.markdown("<h1 style='font-size: 2.5em; text-align: center; margin-bottom: 0px;'>Event Report Generator</h1>", unsafe_allow_html=True)
st.markdown("<hr style='margin:15px 0px;' />", unsafe_allow_html=True)

if 'iqac_file' not in st.session_state:
    st.session_state.iqac_file = None
if 'sm_file' not in st.session_state:
    st.session_state.sm_file = None

# --- 5. DATA LOGGING ENTRY FORM LAYOUT ---
with st.form("main_form"):
    st.subheader("1. Profile")
    c1, c2 = st.columns(2)
    with c1:
        event_title = st.text_input("Event Title", placeholder="Enter official name of the event...")
        event_date = st.date_input("Event Date", datetime.date.today())
        form_dept = st.selectbox("Select Department / Cell", ["-- Select Department --"] + DEPARTMENTS)
    with c2:
        organizer = st.text_input("Event In-charge / Faculty Name", placeholder="Enter organizer's name...")
        participants = st.number_input("No. of Participants", min_value=0, step=1)
        academic_year = st.selectbox("Select Academic Year", ["-- Select Academic Year --"] + ACADEMIC_YEARS)

    # Text Guidelines Placement Box Container
    placeholder_guidelines = (
        "Please mention the following in bullet points:\n"
        "# Where did event take place...\n"
        "# mention activities/ competitions held\n"
        "# Who were all involved in this?\n"
        "# any chief guest/ resource person?\n"
        "# any special attractions etc"
    )
    raw_notes = st.text_area("Paste Event Notes / Narrative Data here", placeholder=placeholder_guidelines, height=180)

    # --- SECTION 2: SUPPORTING DOCUMENTS STATUS ---
    st.subheader("2. Supporting Documents Status")
    doc_options = ["-- Select Status --", "Attached", "NA"]
    
    d_cols = st.columns(5)
    att_a = d_cols[0].selectbox("Brochure/Circular", doc_options, key="status_brochure")
    att_b = d_cols[1].selectbox("Photos", doc_options, key="status_photos")
    att_c = d_cols[2].selectbox("List of Participants with signatures", doc_options, key="status_list")
    att_d = d_cols[3].selectbox("Certificates Issued (with title and date)", doc_options, key="status_cert")
    att_e = d_cols[4].selectbox("Winners’ details (If Competition)", doc_options, key="status_winners")

    # --- SECTION 3: UPLOADS ---
    st.subheader("3. Uploads")
    up_col1, up_col2 = st.columns(2)
    with up_col1:
        brochure_file = st.file_uploader("Upload Brochure/Circular", type=ALLOWED_EXTENSIONS)
        attendance_file = st.file_uploader("Upload List of Participants with signatures", type=ALLOWED_EXTENSIONS)
        winners_file = st.file_uploader("Upload Winners’ details (If Competition)", type=ALLOWED_EXTENSIONS, accept_multiple_files=True)
    with up_col2:
        event_photos = st.file_uploader("Upload Photos", type=ALLOWED_EXTENSIONS, accept_multiple_files=True)
        certificates_file = st.file_uploader("Upload Certificates Issued (with title and date)", type=ALLOWED_EXTENSIONS, accept_multiple_files=True)

    submit = st.form_submit_button("🚀 Generate Both Compiled Reports & Trigger Distributions", use_container_width=True)

# --- 6. DATA COMPILATION & REPOSITORY PIPELINE LOGIC ---
if submit:
    unselected_docs = []
    if att_a == "-- Select Status --": unselected_docs.append("Brochure/Circular")
    if att_b == "-- Select Status --": unselected_docs.append("Photos")
    if att_c == "-- Select Status --": unselected_docs.append("List of Participants with signatures")
    if att_d == "-- Select Status --": unselected_docs.append("Certificates Issued (with title and date)")
    if att_e == "-- Select Status --": unselected_docs.append("Winners’ details (If Competition)")

    if form_dept == "-- Select Department --":
        st.error("Form Validation Error: Please select an explicit Department/Cell.")
    elif academic_year == "-- Select Academic Year --":
        st.error("Form Validation Error: Please select the explicit Academic Year.")
    elif not event_title.strip():
        st.error("Form Validation Error: Event Title cannot be blank.")
    elif not raw_notes.strip():
        st.error("Form Validation Error: Narrative context notes are required!")
    elif unselected_docs:
        st.error(f"Form Validation Error: Please select either 'Attached' or 'NA' for the following items: {', '.join(unselected_docs)}")
    else:
        try:
            with st.spinner("Executing system processes, logging session telemetry, and compiling reports..."):
                iqac_rep = generate_ai_content("Narrative", raw_notes, style="formal")
                obj = generate_ai_content("Objectives", raw_notes, style="formal")
                out = generate_ai_content("Learning Outcomes", raw_notes, style="formal")
                sm_rep = generate_ai_content("Social Media", raw_notes, dept_name=form_dept, title_text=event_title.strip(), style="social")

            def create_doc(template_path, is_iqac=True):
                doc = DocxTemplate(template_path)
                dynamic_dept_header = form_dept if form_dept in ["IQAC", "Research & Innovation"] else f"Department of {form_dept}"
                
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
                    'attach_a': str(att_a), 'attach_b': str(att_b), 'attach_c': str(att_c), 'attach_d': str(att_d), 'attach_e': str(att_e),
                    'brochure_img': "", 'attendance_img': "", 'image_1': "", 'image_2': "", 'image_3': "", 'image_4': "", 'image_5': "", 'image_6': ""
                }
                
                if brochure_file and brochure_file.name.split(".")[-1].lower() in ['jpg', 'jpeg', 'png']: 
                    ctx['brochure_img'] = InlineImage(doc, io.BytesIO(brochure_file.getvalue()), width=Inches(4.5))
                if attendance_file and attendance_file.name.split(".")[-1].lower() in ['jpg', 'jpeg', 'png']: 
                    ctx['attendance_img'] = InlineImage(doc, io.BytesIO(attendance_file.getvalue()), width=Inches(4.5))
                
                if event_photos:
                    img_idx = 1
                    for p in event_photos:
                        if p.name.split(".")[-1].lower() in ['jpg', 'jpeg', 'png'] and img_idx <= 6:
                            ctx[f'image_{img_idx}'] = InlineImage(doc, io.BytesIO(p.getvalue()), width=Inches(3.2))
                            img_idx += 1
                
                doc.render(ctx)
                buf = io.BytesIO()
                doc.save(buf)
                buf.seek(0)
                return buf

            st.session_state.iqac_file = create_doc("Sample_Event_Report_Template.docx", is_iqac=True)
            st.session_state.sm_file = create_doc("Social_Media_Report_Template.docx", is_iqac=False)
            
            # Silent logging tracker execute execution step
            write_audit_log(organizer, form_dept, event_title)
            
            # Automated routing distribution trigger
            mail_status = email_compiled_reports(event_title, form_dept, st.session_state.iqac_file, st.session_state.sm_file)
            if mail_status:
                st.success(f"📧 Reports systematically distributed and emailed to {TARGET_EMAIL} flawlessly!")
            
            st.success("✅ Processes finalized successfully!")

        except Exception as e:
            st.error(f"System Operational Exception: {e}")

# --- 7. ASSET DOWNLOAD ROUTINES ---
if st.session_state.iqac_file and st.session_state.sm_file:
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
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
    
    # Automated ZIP compiler for uploaded image arrays
    if event_photos:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, file_asset in enumerate(event_photos):
                file_bytes = file_asset.read()
                file_ext = file_asset.name.split(".")[-1]
                archive_name = f"Document_{idx+1}.{file_ext}"
                zip_file.writestr(archive_name, file_bytes)
        
        zip_buffer.seek(0)
        clean_folder_title = event_title.replace(" ", "_")
        
        dl_col3.download_button(
            label="📦 Download Photos Zip Folder",
            data=zip_buffer,
            file_name=f"{clean_folder_title}.zip",
            mime="application/zip",
            use_container_width=True
        )
    else:
        dl_col3.markdown("<button disabled style='width:100%; height:43px; border-radius:4px; background-color:#eaeaea; border:none; color:#aaa; font-weight:bold;'>No Photos Uploaded to Archive</button>", unsafe_allow_html=True)

st.markdown("<br><hr/><p style='text-align: center; font-size: 1.05em; font-weight: bold; color: #555;'>Developed by IQAC @ St. Mary's</p>", unsafe_allow_html=True)
