import json
import time

import streamlit as st
from google import genai
from google.genai import errors, types

# Models are tried if Gemini is busy or out of free quota.
MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
TEMPORARY_ERRORS = {429, 500, 503, 504}
MAX_RESUME_MB = 15

st.set_page_config(page_title="AI Career Planner", page_icon="🎯", layout="centered")

# A little CSS (page styling). "centered" layout keeps everything in a middle
# column; we make that column a bit wider so the 3 role cards fit side by side.
st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"] { max-width: 1000px; padding-top: 2.5rem; }
    .hero { text-align: center; margin-bottom: 1.5rem; }
    .hero h1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
    .hero p { color: #475569; font-size: 1.1rem; margin: 0; }
    .step { color: #2563EB; font-weight: 600; font-size: 0.85rem;
            letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem; }
    .score { font-size: 2.4rem; font-weight: 700; color: #2563EB; line-height: 1.1; }
    .score span { font-size: 1rem; font-weight: 500; color: #475569; }
    .footer { text-align: center; color: #64748B; font-size: 0.85rem; padding: 0.5rem 0 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# AI instructions for creating a career plan.
SYSTEM_PROMPT = """You are a friendly, honest career counsellor for students and job seekers in India.
You get a person's profile, and sometimes their resume as a PDF. Build a career plan for them.

What to include:
- roles: exactly 3 roles that fit this person. For each: the job title, one sentence on why it fits
  them, a match_score from 0 to 100, and a typical entry-level salary range in India in LPA
  as text, for example "3-5 LPA". This is only indicative.
- skill_gaps: 4 to 6 skills they need for these roles, most important first. For each: their
  current_level and the needed_level on a 0-10 scale, and one free resource to start learning it.
- roadmap: three blocks (days 1-30, 31-60, 61-90). Each block has exactly 3 concrete tasks that fit
  the hours per week they gave, and one small mini_project to build at the end of the block.
- todays_action: one action they can finish today in under 30 minutes.

If a resume is attached, use it to judge their skills and experience. If the resume and the
typed skills disagree, trust the resume.

Rules: be encouraging but realistic, use simple English, and never promise a job or a salary."""

# AI instructions for answering questions about the finished plan.
FOLLOWUP_PROMPT = """You are a friendly, honest career counsellor for students and job seekers in India.
You already made the career plan below (as JSON) for this person. Answer their follow-up question
about it in simple English, in under 150 words. Be encouraging but realistic, and never promise
a job or a salary."""

# JSON shape for the structured Gemini answer.
S = types.Schema
T = types.Type

ROADMAP_BLOCK = S(
    type=T.OBJECT,
    properties={
        "tasks": S(type=T.ARRAY, items=S(type=T.STRING), min_items=3, max_items=3),
        "mini_project": S(type=T.STRING),
    },
    required=["tasks", "mini_project"],
)

PLAN_SCHEMA = S(
    type=T.OBJECT,
    properties={
        "roles": S(
            type=T.ARRAY,
            min_items=3,
            max_items=3,
            items=S(
                type=T.OBJECT,
                properties={
                    "title": S(type=T.STRING),
                    "why_it_fits": S(type=T.STRING),
                    "match_score": S(type=T.INTEGER, minimum=0, maximum=100),
                    "salary_range_lpa": S(type=T.STRING),
                },
                required=["title", "why_it_fits", "match_score", "salary_range_lpa"],
            ),
        ),
        "skill_gaps": S(
            type=T.ARRAY,
            min_items=4,
            max_items=6,
            items=S(
                type=T.OBJECT,
                properties={
                    "skill": S(type=T.STRING),
                    "current_level": S(type=T.INTEGER, minimum=0, maximum=10),
                    "needed_level": S(type=T.INTEGER, minimum=0, maximum=10),
                    "free_resource": S(type=T.STRING),
                },
                required=["skill", "current_level", "needed_level", "free_resource"],
            ),
        ),
        "roadmap": S(
            type=T.OBJECT,
            properties={
                "days_1_30": ROADMAP_BLOCK,
                "days_31_60": ROADMAP_BLOCK,
                "days_61_90": ROADMAP_BLOCK,
            },
            required=["days_1_30", "days_31_60", "days_61_90"],
        ),
        "todays_action": S(type=T.STRING),
    },
    required=["roles", "skill_gaps", "roadmap", "todays_action"],
)

ROADMAP_TABS = [
    ("days_1_30", "Days 1-30"),
    ("days_31_60", "Days 31-60"),
    ("days_61_90", "Days 61-90"),
]

# Send one Gemini request with retries for temporary service problems.
def call_gemini(contents, config):
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"],
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    last_error = None
    for model in MODELS:
        for attempt in range(2):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except errors.APIError as error:
                if error.code not in TEMPORARY_ERRORS:
                    raise
                last_error = error
                if attempt == 0:
                    time.sleep(2)
    raise last_error

# Create the plan and convert Gemini's JSON text into a Python dictionary.
def make_plan(profile_text, pdf_bytes):
    contents = [profile_text]
    if pdf_bytes:
        contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=PLAN_SCHEMA,
    )
    response = call_gemini(contents, config)
    if not response.text:
        raise ValueError("empty answer")
    return json.loads(response.text)

# Answer a follow-up question using the plan and earlier chat as context.
def answer_followup(plan, history, question):
    chat = "\n".join(f"{who}: {text}" for who, text in history)
    contents = f"Career plan:\n{json.dumps(plan)}\n\nEarlier chat:\n{chat}\n\nNew question: {question}"
    config = types.GenerateContentConfig(
        system_instruction=FOLLOWUP_PROMPT,
        temperature=0.7,
    )
    response = call_gemini(contents, config)
    return response.text or "Sorry, I could not answer that. Please try again."

# Turn technical errors into simple messages.
def friendly_error(error):
    if isinstance(error, KeyError):
        return "No API key found. Add GEMINI_API_KEY to the app secrets."
    if isinstance(error, errors.APIError):
        if error.code in TEMPORARY_ERRORS:
            return "Gemini is very busy right now. Wait a minute and try again."
        if error.code in (400, 401, 403):
            return "Your Gemini API key was rejected. Check your app secrets."
    if isinstance(error, ValueError):
        return "The AI's answer was incomplete. Please try again."
    return f"Something went wrong: {error}"

# Prepare a Markdown copy of the plan.
def plan_to_markdown(plan, name):
    lines = [f"# Career plan for {name}", "", f"**Do this today:** {plan['todays_action']}", ""]
    lines += ["## 3 roles that fit you", ""]
    for role in plan["roles"]:
        lines += [
            f"### {role['title']} ({role['match_score']}% match)",
            role["why_it_fits"],
            f"Salary: {role['salary_range_lpa']} (indicative)",
            "",
        ]
    lines += ["## Your skill gaps", "", "| Skill | Now | Needed | Free resource |", "|---|---|---|---|"]
    for gap in plan["skill_gaps"]:
        lines.append(
            f"| {gap['skill']} | {gap['current_level']}/10 | "
            f"{gap['needed_level']}/10 | {gap['free_resource']} |"
        )
    lines.append("")
    lines += ["## Your 90-day roadmap", ""]
    for key, label in ROADMAP_TABS:
        block = plan["roadmap"][key]
        lines.append(f"### {label}")
        lines += [f"- [ ] {task}" for task in block["tasks"]]
        lines += [f"- [ ] **Mini project:** {block['mini_project']}", ""]
    lines += ["---", "_AI suggestions, not guarantees._"]
    return "\n".join(lines)

# Page header
st.markdown(
    """
    <div class="hero">
      <h1>🎯 AI Career Planner</h1>
      <p>Tell me about yourself. I'll suggest roles, skill gaps and a 90-day plan.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Step 1: optional resume upload.
with st.container(border=True):
    st.markdown('<div class="step">Step 1 · Resume (optional)</div>', unsafe_allow_html=True)
    resume = st.file_uploader(
        "Upload your resume (optional)",
        type="pdf",
        label_visibility="collapsed",
    )
    st.caption(
        "Your resume is sent to Google Gemini to make your plan and is not stored by "
        "this app. On Gemini's free tier Google may use it to improve its products."
    )
    resume_bytes = resume.getvalue() if resume else None
    if resume_bytes and len(resume_bytes) > MAX_RESUME_MB * 1024 * 1024:
        st.warning(f"That PDF is over {MAX_RESUME_MB} MB. Please upload a smaller file.")
        resume_bytes = None

# Step 2: collect the person's profile.
with st.form("profile"):
    st.markdown('<div class="step">Step 2 · About you</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    name = left.text_input("Your name")
    education = right.selectbox(
        "Highest education",
        [
            "Plus Two / 12th",
            "Diploma",
            "B.Tech / B.E.",
            "B.Sc / BCA",
            "B.Com / BBA",
            "BA",
            "Master's degree",
            "Other",
        ],
    )
    status = st.radio(
        "Where are you right now?",
        ["Student", "Graduate looking for a job", "Working, want to switch", "Career break"],
        horizontal=True,
    )
    left, right = st.columns(2)
    skills = left.text_area("Skills you already have", placeholder="Excel, basic Python, communication...")
    interests = right.text_area("What do you enjoy?", placeholder="Solving puzzles, design, talking to people...")
    goal = st.text_input("Your goal", placeholder="Get my first job in tech within 6 months")
    hours = st.slider("Hours per week you can study", 2, 40, 10)
    submitted = st.form_submit_button("🚀 Plan my career", type="primary", use_container_width=True)

def build_profile():
    text = (
        f"Name: {name}\nEducation: {education}\nCurrent status: {status}\n"
        f"Skills: {skills or '(not typed, see resume)'}\nInterests: {interests}\n"
        f"Goal: {goal}\nHours per week available: {hours}"
    )
    if resume_bytes:
        text += "\nA resume is attached as a PDF."
    return text

# Create the plan and save it after Streamlit reruns.
if submitted:
    missing = []
    if not name.strip():
        missing.append("**Your name**")
    if not goal.strip():
        missing.append("**Your goal**")
    if not (skills.strip() or resume_bytes):
        missing.append("**Skills you already have** (or upload a resume)")
    if missing:
        st.warning("Please fill in: " + ", ".join(missing) + ".")
    else:
        error = None
        with st.spinner("Thinking about your career..."):
            try:
                plan = make_plan(build_profile(), resume_bytes)
            except Exception as caught_error:
                error = friendly_error(caught_error)
        if error:
            st.error(error)
        else:
            st.session_state["plan"] = plan
            st.session_state["plan_name"] = name
            st.session_state["plan_id"] = st.session_state.get("plan_id", 0) + 1
            st.session_state["followups"] = []

# Show the dashboard saved in session state.
if "plan" in st.session_state:
    plan = st.session_state["plan"]
    plan_id = st.session_state["plan_id"]
    st.divider()

    st.success(f"**✅ Do this today:** {plan['todays_action']}")

    st.subheader("🧭 3 roles that fit you")
    for column, role in zip(st.columns(3), plan["roles"]):
        with column, st.container(border=True):
            score = max(0, min(100, int(role["match_score"])))
            st.markdown(f"#### {role['title']}")
            st.markdown(
                f'<div class="score">{score}% <span>match</span></div>',
                unsafe_allow_html=True,
            )
            st.progress(score / 100)
            st.write(role["why_it_fits"])
            st.markdown(f"💰 {role['salary_range_lpa']} *(indicative)*")

    st.subheader("📊 Your skill gaps")
    gaps = plan["skill_gaps"]
    chart_box = st.container(border=True)
    chart_box.bar_chart(
        {
            "Skill": [gap["skill"] for gap in gaps],
            "Current level": [gap["current_level"] for gap in gaps],
            "Needed level": [gap["needed_level"] for gap in gaps],
        },
        x="Skill",
        y=["Current level", "Needed level"],
        horizontal=True,
        stack=False,
        color=["#94A3B8", "#2563EB"],
        x_label="Level (0-10)",
        y_label="",
    )
    chart_box.markdown("**Free resources to start**")
    for gap in gaps:
        chart_box.markdown(f"- **{gap['skill']}:** {gap['free_resource']}")

    st.subheader("🗓️ Your 90-day roadmap")
    for tab, (key, label) in zip(
        st.tabs([label for _, label in ROADMAP_TABS]),
        ROADMAP_TABS,
    ):
        with tab:
            block = plan["roadmap"][key]
            for index, task in enumerate(block["tasks"]):
                st.checkbox(task, key=f"task_{plan_id}_{key}_{index}")
            st.info(f"🛠️ **Mini project:** {block['mini_project']}")

    st.download_button(
        "⬇️ Download my plan",
        data=plan_to_markdown(plan, st.session_state["plan_name"]),
        file_name="career-plan.md",
        mime="text/markdown",
        type="primary",
        use_container_width=True,
    )

    st.subheader("💬 Ask about your plan")
    history = st.session_state["followups"]
    question = st.chat_input("Ask a follow-up question about your plan")
    if question:
        error = None
        with st.spinner("Thinking..."):
            try:
                answer = answer_followup(plan, history, question)
            except Exception as caught_error:
                error = friendly_error(caught_error)
        if error:
            st.error(error)
        else:
            history += [("You", question), ("Counsellor", answer)]

    for who, text in history:
        with st.chat_message("user" if who == "You" else "assistant"):
            st.markdown(text)

# Footer
st.divider()
st.markdown(
    '<div class="footer">Built at the Techolas AI Wing weekend · AI suggestions, not guarantees.</div>',
    unsafe_allow_html=True,
)
