import json
import re
import anthropic
from src.config import CLAUDE_API_KEY, VALID_FOLDERS

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def classify_paper(title, abstract, existing_tags=None):
    tags_context = f"Reuse a tag from this existing list only when it accurately describes this specific paper; otherwise create a new, specific tag: {existing_tags}" if existing_tags else ""

    prompt = f"""
    You are an expert academic research assistant. Classify the following academic paper based on its title and abstract.
    
    Title: {title}
    Abstract: {abstract}
    
    Rules:
    1. Choose exactly ONE target folder from this exact list of valid endpoint subfolders:
    {VALID_FOLDERS}    
    2. Generate exactly 3 to 5 descriptive, lowercase tags. Replace any spaces in the tags with hyphens. {tags_context}
    
    Respond ONLY with a valid JSON object in this exact format:
    {{
        "target_folder": "The exact folder path string you selected",
        "tags": ["tag-one", "tag-two", "tag-three"]
    }}
    """
    
    # Structured outputs replace the old "{" prefill (prefill and temperature are rejected on Haiku 5.5)
    schema = {
        "type": "object",
        "properties": {
            "target_folder": {"type": "string", "enum": VALID_FOLDERS},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["target_folder", "tags"],
        "additionalProperties": False,
    }

    raw_output = ""
    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=2048,  # thinking counts toward max_tokens
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
            system="You are a data-processing AI. You only output raw, valid JSON without any markdown formatting.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        if response.stop_reason == "refusal":
            print(f"Claude declined to classify this paper ({response.stop_details.category}).")
            return None

        # Response may start with thinking blocks — read the text block by type
        raw_output = next((b.text for b in response.content if b.type == "text"), "")
        return json.loads(raw_output)

    except json.JSONDecodeError:
        print(f"Error parsing Claude JSON response. Raw output: {raw_output}")
        return None
    except Exception as e:
        print(f"Anthropic API Error: {e}")
        return None
    
def summarize_paper(title, pdf_text, tags=None):
    """Generates a high-signal research summary optimized for Obsidian Graph View and AI ingestion."""
    
    # Obsidian tags can't contain spaces: "Computer Science - Graphics" -> "Computer-Science-Graphics"
    tag_string = " ".join(["#" + re.sub(r'[\s-]+', '-', t.strip()) for t in tags]) if tags else ""

    prompt = f"""
    You are an elite AI Research Scientist and a deep-tech Venture Capital Partner. Your task is to analyze the provided academic paper and extract high-signal intelligence for an Obsidian-based knowledge graph. 
    
    This file will be read by another AI agent (Claude Code) to identify white-spaces in the literature for novel PhD-level research, AND to identify commercial opportunities for a new tech startup. 

    Title: {title}
    
    --- START OF PAPER TEXT ---
    {pdf_text}
    --- END OF PAPER TEXT ---
    
    Format the response EXACTLY using the following Markdown structure. Do not deviate:

    # 🤖 AI-Generated Intelligence
    
    **Tags:** {tag_string} #research-intelligence

    ## 🎯 1. The Core Delta
    * **The Problem:** [1 sentence defining the exact bottleneck in the State-of-the-Art they are attacking.]
    * **The Innovation:** [1-2 sentences on what they actually invented or changed. What is the 'Delta'?]

    ## ⚙️ 2. Technical & Algorithmic Anatomy
    * **Core Primitives:** [List the exact mathematical frameworks, loss functions, algorithms, or physics solvers used.]
    * **Data & Compute Footprint:** [What datasets were used? Is this a massive compute-heavy approach, or lightweight?]
    * **Engineering Complexity:** [If a startup tried to build this for production today, what is the hardest engineering hurdle?]

    ## 🚧 3. Structural Vulnerabilities (The "Catch")
    * **Explicit Limitations:** [What do the authors admit doesn't work?]
    * **Implicit Assumptions & Failure Modes:** [Critically analyze the methodology. What did they assume? What edge cases or out-of-distribution data will break this model?]

    ## 🔬 4. The Academic White-Space (Research Ideation)
    * **The Unsolved Problem:** [Based on the vulnerabilities, what is the obvious next paper that needs to be written?]
    * **A Novel Combination:** [Suggest one novel way to improve this by borrowing a technique from a completely different domain.]

    ## 🚀 5. The Startup Thesis (Commercialization)
    * **Market Application:** [Who buys this technology today? Detail a specific industry or B2B use case.]
    * **The Defensibility Moat:** [If you built a startup around this paper, what is the moat? Is the algorithm easily replicable? Would the startup need a proprietary dataset to survive?]
    * **MVP Reality Check:** [Is this technology actually ready for commercial software, or is it 5 years away from leaving the lab?]
    
    ---
    CRITICAL FORMATTING & OBSIDIAN RULES:
    1. Respond ONLY with valid, unescaped Markdown text. Do NOT use backslashes to escape formatting (e.g., use **Bold**, never \\*\\*Bold\\*\\*).
    2. OBSIDIAN WIKILINKING: Whenever you mention a core mathematical primitive, algorithm, major scientific concept, or dataset, wrap it in double brackets to create an Obsidian Wikilink (e.g., `[[Transformer architecture]]`, `[[Navier-Stokes equations]]`, `[[Human3.6M dataset]]`). 
    3. Do not over-link generic words. Only link high-value technical entities that build a useful knowledge graph.
    """
    
    try:
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=16000,  # thinking counts toward max_tokens on Sonnet 5.5; 3000 would truncate
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        if response.stop_reason == "refusal":
            print(f"Claude declined to summarize this paper ({response.stop_details.category}).")
            return None
        if response.stop_reason == "max_tokens":
            print("Warning: summary hit max_tokens and may be truncated.")

        # Response may start with thinking blocks — read the text block by type
        output = next((b.text for b in response.content if b.type == "text"), "").strip()
        
        # Failsafe: Strip markdown blocks if Claude includes them
        if output.startswith("```markdown"):
            output = output[11:].strip()
        elif output.startswith("```"):
            output = output[3:].strip()
            
        if output.endswith("```"):
            output = output[:-3].strip()

        # Python-Markdown only nests lists indented by 4 spaces; Sonnet 5.5 indents sub-bullets by 2
        output = re.sub(r'^ {2}(?=[*-] )', '    ', output, flags=re.M)

        return output
        
    except Exception as e:
        print(f"Anthropic API Error during summarization: {e}")
        return None