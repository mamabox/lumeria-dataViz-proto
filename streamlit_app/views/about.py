"""
About page — project context, purpose, and credits.
"""

import streamlit as st
from components.sidebar import render_sidebar

# --- Sidebar (consistent across pages) ---
data = render_sidebar()

# --- Page content ---
st.title("About")

# --- The Tool ---
st.header("What is this?")

st.markdown("""
This tool replays and synthesizes a Luméria game session. Researchers can review the animation at different speeds, navigate freely through the timeline, and see the student's journey reconstructed — their movement in the virtual environment and the events they trigger.

Existing tools in the DEEP Space project cover data analysis outside the game, video recordings, and transcriptions. But none of them retrace the gameplay experience itself. This tool fills that gap — not as a replacement for existing software - but as a missing piece in the analysis pipeline.

Rather than presuming what questions researchers will ask, the tool  replays the experience. It is not built to answer a specific question but to show what happened. What to make of it is up to the researcher.
""")

# --- The Game ---
st.header("Luméria")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    Luméria is a collaborative educational game developed by [TECFA](https://tecfa.unige.ch/) (University of Geneva) as part of the [DEEP Space research project](https://tecfa.unige.ch/tecfa/research/deepspace/).
    
    Players navigate a medieval-inspired virtual city, working together to complete spatial orientation challenges on tablet and in VR.
    """)

with col2:
    st.markdown("""
    **DEEP Space**  
    *Promoting spatial thinking for all with digital technology*
    
    Part of the [Swiss DEEP consortium](https://tecfa.unige.ch/tecfa/research/deepspace/) 
    co-funded by Jacobs Foundation, University of Geneva, and PH St. Gallen.
    
    February 2024 – December 2027
    """)

# --- The Author ---
st.header("Built by")

st.markdown("""
**Fatou-Maty Diouf**

Designer and developer of Luméria's virtual environment — the city, the game logic, the tablet and VR experiences — built with Unity.

This visualization tool was developed as an independent initiative, born from a gap identified from the inside: the research team had tools for everything around the gameplay, but nothing to retrace the gameplay itself. Designing what data to collect and building the tool to exploit it are part of the same professional instinct.

Built as a capstone project for the  [Python Programming certification](https://nomades.ch/certification/certifications-python-programming-language/) at Nomades.
""")

# --- Tech Stack ---
with st.expander("🛠️ Tech Stack"):
    st.markdown("""
    - **Game engine:** Unity (C#)
    - **Data pipeline:** Python, Pandas, NumPy
    - **Visualization:** Plotly, Matplotlib
    - **Web app:** Streamlit
    - **Video processing:** OpenCV
    - **Design:** Illustrator, Blender
    """)

# --- Links ---
st.markdown("---")

col_a, col_b, col_c,col_d = st.columns(4)

with col_a:
    st.link_button("DEEP Space Project", "https://tecfa.unige.ch/tecfa/research/deepspace/")

with col_b:
    st.link_button("TECFA, University of Geneva", "https://tecfa.unige.ch/")

with col_c:
    st.link_button("Python Certification (Nomades)", "https://nomades.ch/certification/certifications-python-programming-language/")

with col_d:
    st.link_button("Contact", "https://www.linkedin.com/in/yourprofile")