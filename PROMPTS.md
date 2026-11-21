# Prompt cards — copy into Copilot Chat (Agent mode)

Rules: one card at a time · test after every answer · **two tries, then ask your helper to reset you**.
Never paste your API key into the chat.

---

## Card 1 — First vibe-code (Checkpoint 1)
```
Change the subtitle under the title to: My first AI product, built by [your name].
Don't change anything else.
```

---

## Card 2 — The form (Checkpoint 2)
```
Replace the box with the name input with a form titled "About you". The form asks for:
- Your name (text)
- Highest education (dropdown: Plus Two / 12th, Diploma, B.Tech / B.E., B.Sc / BCA, B.Com / BBA, BA, Master's degree, Other)
- Where are you right now? (radio buttons side by side: Student, Graduate looking for a job, Working, want to switch, Career break)
- Skills you already have (text area)
- What do you enjoy? (text area)
- Your goal (text)
- Hours per week you can study (slider from 2 to 40, starting at 10)
Put name and education side by side, and skills and interests side by side.
Add a full-width blue button "🚀 Plan my career".
When it is pressed: if name, skills or goal is empty, show a warning that lists what is missing.
Otherwise show the answers as JSON under the heading "What the AI will receive".
Keep the page style, the title and the footer.
```

---

## Card 3 — Connect the AI (Checkpoint 3)
Write your own prompt first, then paste it where it says.
```
Connect my form to Gemini.
1. At the top of app.py, add a variable SYSTEM_PROMPT with exactly this text:
"""
[# AI FREELANCE DESIGN MENTOR

## 1. ROLE – Who should AI act as?

You are a friendly, honest and experienced freelance design mentor who helps graphic designers, UI/UX designers and creative professionals build successful freelance careers.

## 2. CONTEXT – What information should AI use?

Understand the person's profile:

- Education and experience
- Graphic design skills
- UI/UX design skills
- Software knowledge (Figma, Photoshop, Illustrator)
- Portfolio and previous projects
- Design interests
- Freelance goals
- Available working hours
- Target clients and preferred market

## 3. TASK – What should AI do?

Help the person build and grow a freelance design career.

Provide these four sections:

### 3 freelance services that fit you
Suggest three suitable freelance services.

For each service, explain:
- What they can offer.
- Who needs this service.
- Why it suits their skills.
- Where to find clients.

### Your skill gaps
Create a table with:

| Current Skills | Skills to Improve | Why It Matters | Next Action |
|---|---|---|---|

### Your 90-day freelance roadmap

Divide the plan into three stages:

- Days 1–30: Choose services and improve skills.
- Days 31–60: Build portfolio and find potential clients.
- Days 61–90: Contact clients, manage projects and improve freelance work.

Include exactly 3 practical tasks for each stage.

### One thing to do today
Give one small task that takes 15–30 minutes and helps the person move forward.

## 4. CONSTRAINTS – What rules should AI follow?

- Never promise clients or income.
- Never suggest fake reviews or experience.
- Use simple English.
- Keep answers under 450 words.
- Give realistic freelance advice.
- Focus on practical actions.
- Consider the person's current skill level.

## 5. STYLE – How should AI communicate?

- Friendly and supportive.
- Simple and professional.
- Easy-to-understand language.
- Practical suggestions.
- Clear examples.
- Encouraging but honest.

## 6. OUTPUT – How should AI respond?

Reply in Markdown with exactly these four headings:

## 3 freelance services that fit you
## Your skill gaps
## Your 90-day freelance roadmap
## One thing to do today

Use a table for skill gaps and task lists for the roadmap.

## 7. QUALITY – How should AI check its answer?

- Make recommendations based on actual skills.
- Suggest services that clients really need.
- Make the roadmap achievable.
- Include exactly 9 roadmap tasks.
- Keep advice relevant to the freelance design market.
- Never guarantee clients or earnings.

IMPORTANT: Do not give generic advice. Help the person build a real freelance design business step by step.]
"""
2. When the form is submitted and nothing is missing, send all the form answers to Gemini
   with SYSTEM_PROMPT, using the Gemini pattern in .github/copilot-instructions.md and setting
   model="gemini-3.8-flash".
3. Show a spinner "Thinking about your career..." while waiting.
4. Replace the JSON with the AI's answer, shown as Markdown in a bordered box.
5. If anything fails, show a friendly error message instead of crashing.
```

### Prompt-writing template (fill the blanks)
```
You are a [friendly, honest] career counsellor for [students and job seekers in India].
Given a person's profile, reply in Markdown with exactly these sections:
## 3 roles that fit you  — [what to include for each role]
## Your skill gaps        — [a table with which columns?]
## Your 90-day roadmap    — [how to split it, how many tasks]
## One thing to do today  — [how small?]
Rules: [never promise a job or a salary], [simple English], [under 450 words], [your own rule]
```

---

## Card 4 — Make it a product (Checkpoint 4)
```
Turn my app into a career dashboard. Keep the form, the page style and the footer.

1. Resume: above the form, add an optional PDF upload titled "Step 1 · Resume (optional)", with this
   small note under it: "Your resume is sent to Google Gemini to make your plan and is not stored by
   this app. On Gemini's free tier Google may use it to improve its products."
   If a PDF is uploaded, send it to Gemini together with the form answers (in memory only).
   When a resume is uploaded, the skills box becomes optional.

2. Structured answer: keep the role and the rules of my SYSTEM_PROMPT, but make Gemini return JSON
   using response_mime_type="application/json" and a response_schema with:
   - roles: exactly 3, each with title, why_it_fits, match_score (0-100), salary_range_lpa
   - skill_gaps: 4 to 6, each with skill, current_level (0-10), needed_level (0-10), free_resource
   - roadmap: days_1_30, days_31_60, days_61_90, each with tasks (exactly 3) and mini_project
   - todays_action: text

3. Dashboard: save the plan in st.session_state, then show:
   - a green box "Do this today" at the top
   - 3 role cards side by side: title, big match score, progress bar, why it fits,
     salary labelled "indicative"
   - a horizontal bar chart of current vs needed level for each skill,
     with the free resources listed under it
   - the roadmap as 3 tabs (Days 1-30, 31-60, 61-90), each task as a checkbox,
     the mini project highlighted
   - a "Download my plan" button that saves the plan as a Markdown file

4. Below the dashboard, add a chat box "Ask about your plan" that answers follow-up questions
   using the plan as context, in under 150 words.
```

---

## Card 6 — Your own feature (Checkpoint 6, Day 2)
```
Add this feature to my app: [describe it in two sentences: what the user does, and what they see].
Put it [below the roadmap / in a new tab / in the sidebar].
Keep everything that already works. Use only streamlit and google-genai.
```

---

## Card E — Explain it (use any time)
```
Explain [the part of app.py that ____] in simple English for someone who has never coded.
Use at most 5 short bullet points. Don't change any code.
```

## Card F — Fix an error (at most twice, then ask your helper)
```
After my last change, the app shows this error: [paste the red error text].
Fix only this error. Don't change anything else.
```
