import os
import json
import pandas as pd
from datetime import datetime

# 데이터 파일 경로 설정
DATA_DIR = "data"
SUPPLIERS_FILE = os.path.join(DATA_DIR, "suppliers.json")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
BOM_FILE = os.path.join(DATA_DIR, "bom.json")
INVENTORY_TRANSACTIONS_FILE = os.path.join(DATA_DIR, "inventory_transactions.json")

# 데이터 로드 함수들
def load_suppliers():
    """거래처 데이터 로드"""
    if os.path.exists(SUPPLIERS_FILE):
        with open(SUPPLIERS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_items():
    """물품 데이터 로드"""
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_bom():
    """BOM 데이터 로드"""
    if os.path.exists(BOM_FILE):
        with open(BOM_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_inventory_transactions():
    """입출고 내역 로드"""
    if os.path.exists(INVENTORY_TRANSACTIONS_FILE):
        with open(INVENTORY_TRANSACTIONS_FILE, 'r') as f:
            return json.load(f)
    return []

# 데이터 저장 함수들
def save_suppliers(suppliers):
    """거래처 데이터 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SUPPLIERS_FILE, 'w') as f:
        json.dump(suppliers, f, indent=4, ensure_ascii=False)

def save_items(items):
    """물품 데이터 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ITEMS_FILE, 'w') as f:
        json.dump(items, f, indent=4, ensure_ascii=False)

def save_bom(bom):
    """BOM 데이터 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BOM_FILE, 'w') as f:
        json.dump(bom, f, indent=4, ensure_ascii=False)

def save_inventory_transactions(transactions):
    """입출고 내역 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INVENTORY_TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f, indent=4, ensure_ascii=False)

# 유틸리티 함수들
def generate_id(data_list):
    """새로운 ID 생성 (기존 ID 중 가장 큰 값 + 1)"""
    if not data_list:
        return 1
    
    ids = [item.get('id', 0) for item in data_list]
    return max(ids) + 1

def update_item_stock(item_id, quantity, transaction_type="입고"):
    """물품의 재고 수량 업데이트"""
    items = load_items()
    
    for item in items:
        if item['id'] == item_id:
            if transaction_type == "입고":
                item['stock'] = item.get('stock', 0) + quantity
            elif transaction_type == "출고":
                new_stock = item.get('stock', 0) - quantity
                if new_stock < 0:
                    return False, "재고가 부족합니다."
                item['stock'] = new_stock
            break
    
    save_items(items)
    return True, "재고 업데이트 완료"

def calculate_materials_for_production(product_id, quantity):
    """생산에 필요한 자재 수량 계산"""
    bom_data = load_bom()
    items = load_items()
    
    if str(product_id) not in bom_data:
        return None, "해당 제품의 BOM 정보가 없습니다."
    
    required_materials = []
    for component in bom_data[str(product_id)]:
        material_id = component['material_id']
        required_qty = component['quantity'] * quantity
        
        # 자재 정보 찾기
        material_name = "알 수 없음"
        current_stock = 0
        for item in items:
            if item['id'] == material_id:
                material_name = item['name']
                current_stock = item.get('stock', 0)
                break
        
        required_materials.append({
            'id': material_id,
            'name': material_name,
            'required_quantity': required_qty,
            'current_stock': current_stock,
            'sufficient': current_stock >= required_qty
        })
    
    return required_materials, "계산 완료"

def validate_supplier_data(supplier):
    """거래처 데이터 유효성 검사"""
    if not supplier.get('name'):
        return False, "거래처명은 필수 입력 항목입니다."
    
    suppliers = load_suppliers()
    # 수정이 아닌 추가인 경우에만 중복 체크
    if 'id' not in supplier:
        for existing_supplier in suppliers:
            if existing_supplier['name'] == supplier['name']:
                return False, "이미 존재하는 거래처명입니다."
    
    # 사업자등록번호 유효성 검사
    business_number = supplier.get('business_number', '')
    if business_number:
        # 사업자번호 형식 검사 (숫자 10자리)
        if not business_number.isdigit() or len(business_number) != 10:
            return False, "사업자등록번호는 10자리 숫자여야 합니다."
        
        # 사업자번호 중복 검사
        for existing_supplier in suppliers:
            if 'id' in supplier and existing_supplier['id'] == supplier['id']:
                continue  # 자기 자신은 건너뜀
            if existing_supplier.get('business_number') == business_number:
                return False, "이미 등록된 사업자등록번호입니다."
    
    return True, "검증 완료"

def validate_item_data(item):
    """물품 데이터 유효성 검사"""
    if not item.get('name'):
        return False, "물품명은 필수 입력 항목입니다."
    
    items = load_items()
    # 수정이 아닌 추가인 경우에만 중복 체크
    if 'id' not in item:
        for existing_item in items:
            if existing_item['name'] == item['name']:
                return False, "이미 존재하는 물품명입니다."
    
    # 품번 유효성 검사
    item_code = item.get('item_code', '')
    if item_code:
        # 품번 중복 검사
        for existing_item in items:
            if 'id' in item and existing_item['id'] == item['id']:
                continue  # 자기 자신은 건너뜀
            if existing_item.get('item_code') == item_code:
                return False, "이미 등록된 품번입니다."
    
    return True, "검증 완료" 