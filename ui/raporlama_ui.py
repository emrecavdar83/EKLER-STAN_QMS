# DEPRECATED: This file has been modularized and moved to ui/raporlar/
# Please use ui.raporlar.dispatcher.render_raporlama_module instead.
# Created At: 2026-04-07 (Phase 2 Refactor)

import streamlit as st

def render_raporlama_module(engine):
    st.error("Bu modül (raporlama_ui.py) kullanımdan kaldırılmıştır. Lütfen sistemi yenileyin.")
    if st.button("Sistemi Yenile (Rerun)"):
        st.rerun()
