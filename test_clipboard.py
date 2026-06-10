import streamlit as st
import streamlit.components.v1 as components

st.title("Test Clipboard")

html = """
<script>
function copy() {
    navigator.clipboard.writeText("test text").then(() => {
        document.getElementById("btn").innerText = "Copied!";
    }).catch(err => {
        document.getElementById("btn").innerText = "Error: " + err;
    });
}
</script>
<button id="btn" onclick="copy()">Copy</button>
"""
components.html(html)
