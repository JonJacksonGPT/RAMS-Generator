from flask import Flask, request, render_template, send_file
import os
from openai import OpenAI
from docx import Document

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def create_combined_docx(content, filename):
    doc = Document()
    for section in content.strip().split("\n\n"):
        if section.strip().startswith("Stage"):
            doc.add_heading(section.strip(), level=1)
        else:
            doc.add_paragraph(section.strip())
    filepath = os.path.join("/mnt/data", filename)
    doc.save(filepath)
    return filepath

@app.route("/", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/questions", methods=["POST"])
def questions():
    task = request.form.get("task")

    prompt = f"Generate 20 tailored RAMS pre-task planning questions based on the task: {task}. Use UK civil engineering terminology."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a RAMS generator that only outputs plain tailored questions."},
            {"role": "user", "content": prompt}
        ]
    )
    text = response.choices[0].message.content
    questions = [line.strip("1234567890. ").strip() for line in text.strip().split("\n") if line.strip()][:20]

    return render_template("questions.html", task=task, questions=questions)

@app.route("/generate", methods=["POST"])
def generate():
    user_inputs = [request.form.get(f"q{i}") for i in range(1, 21)]
    formatted_input = "\n".join([f"{i+1}. {user_inputs[i]}" for i in range(20)])

    prompt = f"""
Create a complete RAMS document based on the following 20 responses:

{formatted_input}

Structure it in three stages:
🟦 Stage 1 – Risk Assessment (min 550 words)  
🟦 Stage 2 – Sequence of Activities (min 600 words)  
🟦 Stage 3 – Method Statement (min 750 words)  

Include these headings inside Stage 3:
1. Scope of Works  
2. Personnel and Responsibilities  
3. Hold Points  
4. Operated Plant  
5. Non-Operated Plant  
6. Materials Required  
7. PPE Required  
8. Rescue Plan  
9. Applicable C2V+ Site Standards  
10. CESWI References  
11. Quality Control  
12. Roles and Responsibilities  
13. Environmental Considerations (5 paragraphs)

Use UK construction terminology. Output in plain text with clear section headers.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional RAMS writer for UK civil engineering."},
                {"role": "user", "content": prompt}
            ]
        )

        output = response.choices[0].message.content

        # Ensure format exists
        if "Stage 2" not in output or "Stage 3" not in output:
            return "<p>❌ RAMS generation failed: OpenAI response incomplete. Check prompt format.</p>"

        # Write to single .docx
        final_path = create_combined_docx(output, "RAMS_Combined.docx")
        return f"✅ RAMS generated. <a href='/download?file=RAMS_Combined.docx'>Click to download</a>"

    except Exception as e:
        return f"<p>❌ Error generating RAMS: {e}</p>"

@app.route("/download")
def download():
    file = request.args.get("file")
    return send_file(os.path.join("/mnt/data", file), as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
