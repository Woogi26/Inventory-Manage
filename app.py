import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# 모듈 임포트
from dashboard import dashboard_app
from supplier_management import supplier_management_app
from item_management import item_management_app
from bom_management import bom_management_app
from inventory_transaction import inventory_transaction_app
from production_management import production_management_app

# 앱 설정
st.set_page_config(
    page_title="재고관리 시스템",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 파일 경로 설정
DATA_DIR = "data"
SUPPLIERS_FILE = os.path.join(DATA_DIR, "suppliers.json")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
BOM_FILE = os.path.join(DATA_DIR, "bom.json")
INVENTORY_TRANSACTIONS_FILE = os.path.join(DATA_DIR, "inventory_transactions.json")

# 데이터 디렉터리 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 데이터 파일 초기화 함수
def initialize_data_files():
    # 거래처 데이터 초기화
    if not os.path.exists(SUPPLIERS_FILE):
        with open(SUPPLIERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
    
    # 물품 데이터 초기화
    if not os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
    
    # BOM 데이터 초기화
    if not os.path.exists(BOM_FILE):
        with open(BOM_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
    
    # 입출고 내역 초기화
    if not os.path.exists(INVENTORY_TRANSACTIONS_FILE):
        with open(INVENTORY_TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

# 데이터 파일 초기화
initialize_data_files()

# 사이드바 - 메뉴 선택
st.sidebar.title("재고관리 시스템")
menu = st.sidebar.radio(
    "메뉴 선택",
    ["대시보드", "거래처 관리", "물품 관리", "BOM 관리", "입출고 관리", "생산 관리"]
)

# 앱 타이틀 및 설명
st.sidebar.markdown("---")
st.sidebar.info(
    """
    이 시스템은 Streamlit으로 개발된 재고관리 프로그램으로,
    물품, 거래처, BOM, 입출고 관리 등의 기능을 제공합니다.
    """
)

# 페이지 하단 정보
st.sidebar.markdown("---")
st.sidebar.info(f"© {datetime.now().year} 재고관리 시스템")

# 메인 앱 레이아웃
if menu == "대시보드":
    dashboard_app()
elif menu == "거래처 관리":
    supplier_management_app()
elif menu == "물품 관리":
    item_management_app()
elif menu == "BOM 관리":
    bom_management_app()
elif menu == "입출고 관리":
    inventory_transaction_app()
elif menu == "생산 관리":
    production_management_app() 