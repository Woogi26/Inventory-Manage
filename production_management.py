import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    load_items, load_bom, load_inventory_transactions, save_inventory_transactions,
    generate_id, update_item_stock, calculate_materials_for_production
)

def production_management_app():
    st.title("생산 관리")
    st.write("BOM 기반으로 생산에 필요한 자재 목록을 생성할 수 있습니다.")
    
    # 데이터 로드
    items = load_items()
    bom_data = load_bom()
    transactions = load_inventory_transactions()
    
    # BOM이 설정된 제품만 필터링
    products_with_bom = []
    for product_id_str in bom_data.keys():
        product = next((item for item in items if str(item['id']) == product_id_str), None)
        if product:
            products_with_bom.append(product)
    
    if not products_with_bom:
        st.warning("BOM이 설정된 제품이 없습니다. 먼저 물품과 BOM을 등록해주세요.")
        return
    
    # 탭 분리 (생산 계획/생산 실행)
    tab1, tab2 = st.tabs(["생산 계획", "생산 실행"])
    
    # 생산 계획 탭
    with tab1:
        st.subheader("생산 계획")
        
        # 제품 선택
        product_options = [f"{p['name']} ({p.get('unit', '')})" for p in products_with_bom]
        selected_product_idx = st.selectbox(
            "생산할 제품 선택", 
            range(len(product_options)),
            format_func=lambda x: product_options[x]
        )
        
        selected_product = products_with_bom[selected_product_idx]
        
        # 생산 수량 입력
        production_quantity = st.number_input(
            "생산 수량", 
            min_value=1, 
            value=1, 
            step=1
        )
        
        if st.button("필요 자재 계산"):
            # 필요 자재 계산
            required_materials, message = calculate_materials_for_production(
                selected_product['id'], 
                production_quantity
            )
            
            if required_materials:
                st.success(f"{selected_product['name']} {production_quantity}{selected_product.get('unit', '')} 생산에 필요한 자재 목록입니다.")
                
                # 필요 자재 데이터프레임
                materials_df = pd.DataFrame(required_materials)
                
                # 컬럼 이름 한글로 변경
                materials_df = materials_df.rename(columns={
                    'id': '자재ID',
                    'name': '자재명',
                    'required_quantity': '필요수량',
                    'current_stock': '현재재고',
                    'sufficient': '재고충분'
                })
                
                # 재고 충분 여부 강조
                def highlight_sufficient(val):
                    if val == True:
                        return 'background-color: rgba(0, 255, 0, 0.2)'
                    elif val == False:
                        return 'background-color: rgba(255, 0, 0, 0.2)'
                    return ''
                
                styled_df = materials_df.style.applymap(highlight_sufficient, subset=['재고충분'])
                st.dataframe(styled_df)
                
                # 세션 상태에 생산 계획 저장 (생산 실행 탭에서 사용)
                st.session_state['production_plan'] = {
                    'product': selected_product,
                    'quantity': production_quantity,
                    'materials': required_materials
                }
                
                # 재고 부족 자재 확인
                insufficient_materials = [m for m in required_materials if not m['sufficient']]
                if insufficient_materials:
                    st.warning("일부 자재의 재고가 부족합니다. 자재를 추가로 확보하거나 생산 수량을 조정하세요.")
                    
                    # 부족한 자재 테이블 표시
                    insufficient_df = pd.DataFrame([
                        {
                            '자재명': m['name'],
                            '필요수량': m['required_quantity'],
                            '현재재고': m['current_stock'],
                            '부족수량': m['required_quantity'] - m['current_stock']
                        } for m in insufficient_materials
                    ])
                    st.dataframe(insufficient_df)
            else:
                st.error(message)
    
    # 생산 실행 탭
    with tab2:
        st.subheader("생산 실행")
        
        if 'production_plan' not in st.session_state:
            st.info("먼저 '생산 계획' 탭에서 필요 자재를 계산해주세요.")
        else:
            plan = st.session_state['production_plan']
            product = plan['product']
            quantity = plan['quantity']
            materials = plan['materials']
            
            st.write(f"### 생산 정보")
            st.write(f"- 제품: **{product['name']}**")
            st.write(f"- 수량: **{quantity} {product.get('unit', '')}**")
            
            # 재고 부족 확인
            insufficient_materials = [m for m in materials if not m['sufficient']]
            if insufficient_materials:
                st.error("일부 자재의 재고가 부족하여 생산을 진행할 수 없습니다.")
                
                # 부족한 자재 테이블 표시
                insufficient_df = pd.DataFrame([
                    {
                        '자재명': m['name'],
                        '필요수량': m['required_quantity'],
                        '현재재고': m['current_stock'],
                        '부족수량': m['required_quantity'] - m['current_stock']
                    } for m in insufficient_materials
                ])
                st.dataframe(insufficient_df)
            else:
                # 생산 진행 옵션
                st.write("### 생산 진행")
                st.write("모든 자재의 재고가 충분합니다. 생산을 진행할 수 있습니다.")
                
                production_date = st.date_input("생산 일자", datetime.now().date())
                production_note = st.text_area("생산 비고", "")
                
                if st.button("생산 실행"):
                    # 자재 출고 처리
                    material_errors = []
                    
                    for material in materials:
                        # 자재 재고 감소 (출고 처리)
                        success, message = update_item_stock(
                            material['id'], 
                            material['required_quantity'], 
                            transaction_type="출고"
                        )
                        
                        if not success:
                            material_errors.append(f"자재 '{material['name']}' 출고 실패: {message}")
                        else:
                            # 출고 내역 기록
                            new_transaction = {
                                'id': generate_id(transactions),
                                'transaction_type': "출고",
                                'item_id': material['id'],
                                'quantity': material['required_quantity'],
                                'supplier_id': None,
                                'transaction_date': production_date.strftime("%Y-%m-%d"),
                                'note': f"{product['name']} 생산을 위한 자재 출고",
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            transactions.append(new_transaction)
                    
                    # 오류가 없으면 제품 입고 처리
                    if not material_errors:
                        # 제품 재고 증가 (입고 처리)
                        success, message = update_item_stock(
                            product['id'], 
                            quantity, 
                            transaction_type="입고"
                        )
                        
                        if success:
                            # 입고 내역 기록
                            new_transaction = {
                                'id': generate_id(transactions),
                                'transaction_type': "입고",
                                'item_id': product['id'],
                                'quantity': quantity,
                                'supplier_id': None,
                                'transaction_date': production_date.strftime("%Y-%m-%d"),
                                'note': f"생산 완료: {production_note}",
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            transactions.append(new_transaction)
                            
                            # 거래 내역 저장
                            save_inventory_transactions(transactions)
                            
                            st.success(f"{product['name']} {quantity}{product.get('unit', '')} 생산이 완료되었습니다.")
                            
                            # 세션 상태 초기화
                            del st.session_state['production_plan']
                            st.rerun()
                        else:
                            st.error(f"제품 입고 처리 실패: {message}")
                    else:
                        for error in material_errors:
                            st.error(error) 