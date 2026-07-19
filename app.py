import streamlit as st
import streamlit as st

st.set_page_config(
    page_title="Endangered Species Tracker",
    page_icon="🦏",
    layout="wide"
)

# Header
st.title("🦏 Endangered Species Tracker")
st.subheader("Protecting Wildlife Through Data & AI")

st.write(
    """
    Welcome to the **Endangered Species Tracker**.
    This platform helps researchers, students, and wildlife lovers
    explore endangered species, population trends, and conservation data.
    """
)

# Search
species = st.text_input("🔍 Search for a species")

if species:
    st.success(f"You searched for: {species}")

st.divider()

# Statistics
st.header("📊 Quick Statistics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Species", "44,000+")
col2.metric("Vulnerable", "9,000")
col3.metric("Endangered", "16,000")
col4.metric("Critically Endangered", "8,000")

st.divider()

# Featured Species
st.header("🚨 Featured Endangered Species")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("🦏 One-horned Rhinoceros")
    st.write("Population increasing through conservation.")

with c2:
    st.subheader("🐯 Bengal Tiger")
    st.write("One of the world's most iconic endangered species.")

with c3:
    st.subheader("🐼 Red Panda")
    st.write("Native to the Himalayan region.")

st.divider()

# About
st.header("🌍 Why This Project?")

st.write("""
Our mission is to make wildlife conservation data easy to understand.
Users can search species, visualize maps, explore population trends,
and learn how conservation efforts are helping protect biodiversity.
""")