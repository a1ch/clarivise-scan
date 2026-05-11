"""
Clarivise — AI-powered email security platform.
Two product lines: Clarivise Scan and Clarivise Shield.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import streamlit as st
from supabase import Client, create_client

MIN_PASSWORD_LEN = 8
SB_ACCESS = "sb_access_token"
SB_REFRESH = "sb_refresh_token"
SB_ANON = "portal_anon_client"

PAGE_HOME        = "streamlit_app.py"
PAGE_REQUEST_KEY = "pages/1_Request_a_key.py"
PAGE_TERMS       = "pages/2_Terms.py"
PAGE_PRIVACY     = "pages/3_Privacy.py"
PAGE_DOWNLOADS   = "pages/4_Download_Guides.py"
PAGE_FAQ         = "pages/5_FAQ.py"