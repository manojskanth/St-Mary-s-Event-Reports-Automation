import streamlit as st
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
import google.generativeai as genai
import datetime
import io
import re

# --- 1. AI ENGINE (Strict 150-Word Limits) ---
def generate_ai_content(section_name, notes, style="formal"):
    model_name = 'gemini-2.5-flash-lite' 
    
    if style == "social":
        rules = "STRICT LIMIT: Max 150 words. Catchy social media post with 3-5 hashtags. Engaging tone."
    elif section_name in ["Objectives", "Learning Outcomes"]:
        rules = "Exactly 2 bullet points, max 2 lines each. Strict academic tone."
    else: # IQAC Narrative
        rules = "Formal academic summary. STRICT LIMIT: Max 150 words. No intro fluff."

    prompt = f"Task: Write '{section_name}' for St. Mary's College. Notes: {notes}. Rules: {rules}"
    
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    # Clean up text to prevent Word XML corruption
    return re.sub(r'[^\x00-\x7F]+', ' ', response.text).replace("**", "").strip()

# --- 2. UI SETUP ---
st.set_page_config(page_title="St. Mary's Dual Portal", layout="wide")
st.title("🎓 Dual Report Generator")

# Initialize Session State to keep reports available after clicking
if 'iqac_file' not in st.session_state:
    st.session_state.iqac_file = None
if 'sm_file' not in st.session_state:
    st.session_state.sm_file = None

with st.form("main_form"):
    st.subheader("1. Metadata")
    c1, c2 = st.columns(2)
    with c1:
        event_title = st.text_input("Event Title")
        event_date = st.date_input("Event Date", datetime.date.today())
        academic_year = st.text_input("Academic Year", value="2025-26")
    with c2:
        organizer = st.text_input("Event In-charge")
        participants = st.number_input("No. of Participants", min_value=0)

    raw_notes = st.text_area("Paste Event Notes here")

    st.subheader("2. Supporting Documents Status")
    d_cols = st.columns(5)
    att_a = d_cols[0].selectbox("Brochure", ["Attached", "NA"])
    att_b = d_cols[1].selectbox("Photos", ["Attached", "NA"])
    att_c = d_cols[2].selectbox("List", ["Attached", "NA"])
    att_d = d_cols[3].selectbox("Certificates", ["Attached", "NA"])
    att_e = d_cols[4].selectbox("Winners", ["Attached", "NA"])

    st.subheader("3. Uploads")
    up1, up2 = st.columns(2)
    with up1:
        brochure_file = st.file_uploader("Upload Brochure", type=['jpg','png','jpeg'])
        attendance_file = st.file_uploader("Upload Attendance/List", type=['jpg','png','jpeg'])
    with up2:
        event_photos = st.file_uploader("Photos (Up to 6)", type=['jpg','png','jpeg'], accept_multiple_files=True)

    submit = st.form_submit_button("🚀 Generate Both Reports")

# --- 3. DUAL LOGIC ---
if submit:
    if not raw_notes:
        st.error("Please provide notes!")
    else:
        try:
            with st.spinner("AI is generating reports..."):
                iqac_rep = generate_ai_content("Narrative", raw_notes, "formal")
                obj = generate_ai_content("Objectives", raw_notes, "formal")
                out = generate_ai_content("Learning Outcomes", raw_notes, "formal")
                sm_rep = generate_ai_content("Social Media", raw_notes, "social")

            def create_doc(template_path, is_iqac=True):
                doc = DocxTemplate(template_path)
                ctx = {
                    'event_title': str(event_title),
                    'event_date': event_date.strftime("%d-%m-%Y"),
                    'academic_year': str(academic_year),
                    'organizer': str(organizer),
                    'participants': str(participants),
                    'report_body': str(iqac_rep if is_iqac else sm_rep),
                    'objectives': str(obj if is_iqac else ""),
                    'outcomes': str(out if is_iqac else ""),
                    'attach_a': str(att_a), 'attach_b': str(att_b), 'attach_c': str(att_c),
                    'attach_d': str(att_d), 'attach_e': str(att_e),
                    'brochure_img': "", 'attendance_img': "",
                    'image_1': "", 'image_2': "", 'image_3': "",
                    'image_4': "", 'image_5': "", 'image_6': ""
                }
                
                # Image processing with fixed stream conversion
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

            # Store files in Session State so they don't disappear
            st.session_state.iqac_file = create_doc("Sample_Event_Report_Template.docx", True)
            st.session_state.sm_file = create_doc("Social_Media_Report_Template.docx", False)
            st.success("✅ Both reports generated and ready!")

        except Exception as e:
            st.error(f"Error: {e}")

# Display download buttons if files exist in session state
if st.session_state.iqac_file and st.session_state.sm_file:
    dl_col1, dl_col2 = st.columns(2)
    dl_col1.download_button(
        label="⬇️ Download IQAC Report",
        data=st.session_state.iqac_file,
        file_name=f"IQAC_{event_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    dl_col2.download_button(
        label="⬇️ Download Social Media Report",
        data=st.session_state.sm_file,
        file_name=f"Social_{event_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )