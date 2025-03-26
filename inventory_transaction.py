import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    load_items, save_items, 
    load_inventory_transactions, save_inventory_transactions,
    load_suppliers, generate_id, update_item_stock
)

def inventory_transaction_app():
    st.title("입출고 관리")
    
    # 탭 분리 (조회/등록)
    tab1, tab2, tab3 = st.tabs(["입출고 내역", "입출고 등록", "대량 등록"])
    
    # 데이터 로드
    items = load_items()
    transactions = load_inventory_transactions()
    suppliers = load_suppliers()
    
    # 입출고 내역 탭
    with tab1:
        st.subheader("입출고 내역")
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transaction_type_filter = st.selectbox(
                "거래 유형", 
                ["전체", "입고", "출고"]
            )
        
        with col2:
            # 물품 필터
            item_name_filter = st.selectbox(
                "물품",
                ["전체"] + [item['name'] for item in items]
            )
        
        with col3:
            # 날짜 범위 필터 (미구현 상태, 향후 기능 추가)
            date_filter = st.selectbox(
                "기간",
                ["전체", "오늘", "이번 주", "이번 달", "직접 입력"]
            )
        
        # 거래 내역 필터링
        filtered_transactions = transactions
        
        # 거래 유형 필터 적용
        if transaction_type_filter != "전체":
            filtered_transactions = [t for t in filtered_transactions if t['transaction_type'] == transaction_type_filter]
        
        # 물품 필터 적용
        if item_name_filter != "전체":
            item_id = next((item['id'] for item in items if item['name'] == item_name_filter), None)
            if item_id:
                filtered_transactions = [t for t in filtered_transactions if t['item_id'] == item_id]
        
        # 날짜 필터 적용 (향후 구현)
        
        # 필터링된 거래 내역 표시
        if filtered_transactions:
            # 데이터 변환 (ID를 이름으로 매핑)
            display_transactions = []
            
            for t in filtered_transactions:
                item_name = "알 수 없음"
                supplier_name = "알 수 없음"
                
                # 물품명 찾기
                item = next((i for i in items if i['id'] == t['item_id']), None)
                if item:
                    item_name = item['name']
                
                # 거래처명 찾기
                if t.get('supplier_id'):
                    supplier = next((s for s in suppliers if s['id'] == t['supplier_id']), None)
                    if supplier:
                        supplier_name = supplier['name']
                
                display_transactions.append({
                    'id': t['id'],
                    '날짜': t.get('transaction_date', ''),
                    '유형': t['transaction_type'],
                    '물품명': item_name,
                    '수량': t['quantity'],
                    '단위': item.get('unit', '') if item else '',
                    '거래처': supplier_name,
                    '참고사항': t.get('note', '')
                })
            
            # DataFrame으로 변환하여 표시
            df = pd.DataFrame(display_transactions)
            # ID 컬럼은 표시하지 않음
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            
            st.dataframe(df)
            
            # 거래 삭제 기능
            st.subheader("거래 내역 삭제")
            
            # 거래 ID 선택 (날짜와 물품명으로 구분)
            transaction_options = [f"{t['날짜']} - {t['물품명']} ({t['유형']}, {t['수량']})" for t in display_transactions]
            if transaction_options:
                selected_transaction_idx = st.selectbox(
                    "삭제할 거래 내역 선택",
                    options=range(len(transaction_options)),
                    format_func=lambda x: transaction_options[x]
                )
                
                selected_transaction = display_transactions[selected_transaction_idx]
                selected_transaction_id = selected_transaction['id']
                
                if st.button("선택한 거래 내역 삭제"):
                    # 선택한 거래 내역 찾기
                    transaction_to_delete = next((t for t in transactions if t['id'] == selected_transaction_id), None)
                    
                    if transaction_to_delete:
                        # 재고 수량 복원
                        item_id = transaction_to_delete['item_id']
                        quantity = transaction_to_delete['quantity']
                        trans_type = transaction_to_delete['transaction_type']
                        
                        # 입고 삭제 -> 재고 감소, 출고 삭제 -> 재고 증가
                        reverse_type = "출고" if trans_type == "입고" else "입고"
                        success, message = update_item_stock(item_id, quantity, transaction_type=reverse_type)
                        
                        if success:
                            # 거래 내역에서 삭제
                            transactions = [t for t in transactions if t['id'] != selected_transaction_id]
                            save_inventory_transactions(transactions)
                            st.success("거래 내역이 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error(f"재고 업데이트 실패: {message}")
        else:
            st.info("조회된 입출고 내역이 없습니다.")
    
    # 입출고 등록 탭
    with tab2:
        st.subheader("입출고 등록")
        
        with st.form("add_transaction_form"):
            # 거래 유형 선택
            transaction_type = st.radio("거래 유형", ["입고", "출고"])
            
            # 물품 선택
            if not items:
                st.warning("등록된 물품이 없습니다. 먼저 물품을 등록해주세요.")
                st.stop()
            
            item_options = [f"{item['name']} (재고: {item.get('stock', 0)} {item.get('unit', '')})" for item in items]
            selected_item_idx = st.selectbox("물품 선택", range(len(item_options)), format_func=lambda x: item_options[x])
            selected_item = items[selected_item_idx]
            
            # 거래처 선택
            supplier_options = ["선택 안함"] + [s['name'] for s in suppliers]
            selected_supplier = st.selectbox("거래처", supplier_options)
            
            # 수량 입력
            quantity = st.number_input("수량", min_value=0.01, step=0.01)
            
            # 날짜 선택 (기본값 현재 날짜)
            transaction_date = st.date_input("거래 일자", datetime.now().date())
            
            # 참고사항
            note = st.text_area("참고사항")
            
            submitted = st.form_submit_button("등록")
            
            if submitted:
                # 거래처 ID 설정
                supplier_id = None
                if selected_supplier != "선택 안함":
                    supplier = next((s for s in suppliers if s['name'] == selected_supplier), None)
                    if supplier:
                        supplier_id = supplier['id']
                
                # 출고 시 재고 확인
                if transaction_type == "출고":
                    current_stock = selected_item.get('stock', 0)
                    if quantity > current_stock:
                        st.error(f"재고 부족! 현재 재고: {current_stock} {selected_item.get('unit', '')}")
                        st.stop()
                
                # 재고 업데이트
                success, message = update_item_stock(
                    selected_item['id'], 
                    quantity, 
                    transaction_type=transaction_type
                )
                
                if success:
                    # 새로운 거래 내역 데이터 생성
                    new_transaction = {
                        'id': generate_id(transactions),
                        'transaction_type': transaction_type,
                        'item_id': selected_item['id'],
                        'quantity': quantity,
                        'supplier_id': supplier_id,
                        'transaction_date': transaction_date.strftime("%Y-%m-%d"),
                        'note': note,
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 거래 내역 추가
                    transactions.append(new_transaction)
                    save_inventory_transactions(transactions)
                    
                    st.success(f"{transaction_type} 내역이 등록되었습니다.")
                    st.rerun()
                else:
                    st.error(f"재고 업데이트 실패: {message}")
    
    # 대량 등록 탭
    with tab3:
        st.subheader("입출고 대량 등록")
        
        # 템플릿 다운로드 옵션
        st.write("입출고 대량 등록을 위한 템플릿을 다운로드하세요.")
        
        template_df = pd.DataFrame({
            '거래유형': ['입고 또는 출고'],
            '물품명': ['등록된 물품명과 정확히 일치해야 합니다'],
            '수량': [1.0],
            '거래처명': ['없으면 비워두세요'],
            '거래일자': [datetime.now().strftime("%Y-%m-%d")],
            '참고사항': ['']
        })
        
        template_csv = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="템플릿 CSV 다운로드",
            data=template_csv,
            file_name='inventory_transaction_template.csv',
            mime='text/csv'
        )
        
        # 물품 및 거래처 목록 안내
        with st.expander("등록된 물품 및 거래처 목록"):
            st.write("### 물품 목록")
            items_df = pd.DataFrame([
                {
                    '물품명': item['name'],
                    '현재재고': item.get('stock', 0),
                    '단위': item.get('unit', '')
                } for item in items
            ])
            st.dataframe(items_df)
            
            st.write("### 거래처 목록")
            suppliers_df = pd.DataFrame([{'거래처명': s['name']} for s in suppliers])
            st.dataframe(suppliers_df)
        
        # 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("업로드된 데이터 미리보기:")
                st.dataframe(df.head())
                
                if st.button("대량 등록 실행"):
                    # 필수 컬럼 확인
                    required_columns = ['거래유형', '물품명', '수량']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"CSV 파일에 다음 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
                    else:
                        # 데이터 처리
                        success_count = 0
                        error_count = 0
                        error_messages = []
                        
                        for idx, row in df.iterrows():
                            # 필수 데이터 확인
                            transaction_type = row['거래유형']
                            if transaction_type not in ['입고', '출고']:
                                error_count += 1
                                error_messages.append(f"오류 (행 {idx+2}): '거래유형'은 '입고' 또는 '출고'만 가능합니다.")
                                continue
                            
                            # 물품 찾기
                            item_name = row['물품명']
                            item = next((i for i in items if i['name'] == item_name), None)
                            
                            if not item:
                                error_count += 1
                                error_messages.append(f"오류 (행 {idx+2}): 물품 '{item_name}'을(를) 찾을 수 없습니다.")
                                continue
                            
                            # 수량 확인
                            try:
                                quantity = float(row['수량'])
                                if quantity <= 0:
                                    error_count += 1
                                    error_messages.append(f"오류 (행 {idx+2}): 수량은 0보다 커야 합니다.")
                                    continue
                            except:
                                error_count += 1
                                error_messages.append(f"오류 (행 {idx+2}): 수량을 숫자로 변환할 수 없습니다.")
                                continue
                            
                            # 거래처 찾기
                            supplier_id = None
                            if pd.notna(row.get('거래처명', '')) and row.get('거래처명', '') != '':
                                supplier = next((s for s in suppliers if s['name'] == row['거래처명']), None)
                                if supplier:
                                    supplier_id = supplier['id']
                            
                            # 날짜 처리
                            transaction_date = datetime.now().strftime("%Y-%m-%d")
                            if pd.notna(row.get('거래일자', '')) and row.get('거래일자', '') != '':
                                try:
                                    # 여러 날짜 형식 지원
                                    parsed_date = pd.to_datetime(row['거래일자'])
                                    transaction_date = parsed_date.strftime("%Y-%m-%d")
                                except:
                                    # 날짜 형식이 잘못된 경우 현재 날짜로 대체
                                    pass
                            
                            # 출고 시 재고 확인
                            if transaction_type == "출고":
                                current_stock = item.get('stock', 0)
                                if quantity > current_stock:
                                    error_count += 1
                                    error_messages.append(f"오류 (행 {idx+2}): 재고 부족 - 물품 '{item_name}', 현재 재고: {current_stock}, 필요 수량: {quantity}")
                                    continue
                            
                            # 재고 업데이트
                            success, message = update_item_stock(
                                item['id'], 
                                quantity, 
                                transaction_type=transaction_type
                            )
                            
                            if success:
                                # 새로운 거래 내역 데이터 생성
                                new_transaction = {
                                    'id': generate_id(transactions),
                                    'transaction_type': transaction_type,
                                    'item_id': item['id'],
                                    'quantity': quantity,
                                    'supplier_id': supplier_id,
                                    'transaction_date': transaction_date,
                                    'note': row.get('참고사항', ''),
                                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # 거래 내역 추가
                                transactions.append(new_transaction)
                                success_count += 1
                            else:
                                error_count += 1
                                error_messages.append(f"오류 (행 {idx+2}): 재고 업데이트 실패 - {message}")
                        
                        # 결과 저장 및 표시
                        if success_count > 0:
                            save_inventory_transactions(transactions)
                            st.success(f"{success_count}개의 입출고 내역이 성공적으로 등록되었습니다.")
                        
                        if error_count > 0:
                            st.error(f"{error_count}개의 입출고 내역 등록 중 오류가 발생했습니다.")
                            for msg in error_messages:
                                st.warning(msg)
                        
                        # 페이지 리로드
                        if success_count > 0:
                            st.rerun()
                            
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}") 