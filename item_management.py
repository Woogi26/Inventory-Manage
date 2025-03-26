import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_items, save_items, load_suppliers, generate_id, validate_item_data

def item_management_app():
    st.title("물품 관리")
    
    # 탭 분리 (조회/등록/수정/삭제)
    tab1, tab2, tab3 = st.tabs(["물품 목록", "물품 등록", "대량 등록"])
    
    # 물품 데이터 로드
    items = load_items()
    suppliers = load_suppliers()
    
    # 물품 목록 표시 탭
    with tab1:
        st.subheader("물품 목록")
        
        # 검색 필터
        search_term = st.text_input("물품명 검색", "")
        
        filtered_items = items
        if search_term:
            filtered_items = [item for item in items if search_term.lower() in item.get('name', '').lower()]
            
        if filtered_items:
            # DataFrame으로 변환하여 표시
            df = pd.DataFrame(filtered_items)
            
            # ID 컬럼은 화면에 표시하지 않음
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            
            st.dataframe(df)
            
            # 수정/삭제할 물품 선택
            item_names = [item['name'] for item in filtered_items]
            selected_item = st.selectbox("수정/삭제할 물품 선택", item_names)
            
            # 선택한 물품 정보 가져오기
            selected_item_data = next((item for item in filtered_items if item['name'] == selected_item), None)
            
            if selected_item_data:
                edit_col, delete_col = st.columns(2)
                
                with edit_col:
                    if st.button("선택한 물품 수정"):
                        # 세션 상태에 수정할 물품 정보 저장
                        st.session_state['edit_item'] = selected_item_data
                        st.rerun()
                
                with delete_col:
                    if st.button("선택한 물품 삭제"):
                        # 물품 삭제 프로세스
                        items = [item for item in items if item['id'] != selected_item_data['id']]
                        save_items(items)
                        st.success(f"물품 '{selected_item}'이(가) 삭제되었습니다.")
                        st.rerun()
        else:
            st.info("등록된 물품이 없습니다.")
        
        # 물품 수정 폼
        if 'edit_item' in st.session_state:
            st.subheader("물품 정보 수정")
            
            edit_data = st.session_state['edit_item']
            
            with st.form("edit_item_form"):
                name = st.text_input("물품명*", edit_data.get('name', ''))
                item_code = st.text_input("품번", edit_data.get('item_code', ''))
                category = st.text_input("카테고리", edit_data.get('category', ''))
                
                # 거래처 선택 옵션
                supplier_options = ["선택 안함"] + [s['name'] for s in suppliers]
                current_supplier = next((s['name'] for s in suppliers if s['id'] == edit_data.get('supplier_id')), "선택 안함")
                selected_supplier = st.selectbox("거래처", options=supplier_options, index=supplier_options.index(current_supplier) if current_supplier in supplier_options else 0)
                
                unit = st.text_input("단위", edit_data.get('unit', ''))
                stock = st.number_input("재고 수량", value=float(edit_data.get('stock', 0)), step=1.0)
                unit_price = st.number_input("단가", value=float(edit_data.get('unit_price', 0)), step=100.0)
                description = st.text_area("설명", edit_data.get('description', ''))
                
                submitted = st.form_submit_button("수정 완료")
                
                if submitted:
                    # 거래처 ID 설정
                    supplier_id = None
                    if selected_supplier != "선택 안함":
                        supplier_data = next((s for s in suppliers if s['name'] == selected_supplier), None)
                        if supplier_data:
                            supplier_id = supplier_data['id']
                    
                    # 수정된 데이터 구성
                    updated_item = {
                        'id': edit_data['id'],
                        'name': name,
                        'item_code': item_code,
                        'category': category,
                        'supplier_id': supplier_id,
                        'unit': unit,
                        'stock': stock,
                        'unit_price': unit_price,
                        'description': description,
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 데이터 유효성 검사
                    is_valid, message = validate_item_data(updated_item)
                    
                    if is_valid:
                        # 물품 정보 업데이트
                        for i, item in enumerate(items):
                            if item['id'] == edit_data['id']:
                                items[i] = updated_item
                                # created_at 값 보존
                                if 'created_at' in item:
                                    items[i]['created_at'] = item['created_at']
                                break
                        
                        save_items(items)
                        st.success(f"물품 '{name}'의 정보가 수정되었습니다.")
                        
                        # 세션 상태 초기화
                        del st.session_state['edit_item']
                        st.rerun()
                    else:
                        st.error(message)
            
            if st.button("수정 취소"):
                del st.session_state['edit_item']
                st.rerun()
    
    # 물품 등록 탭
    with tab2:
        st.subheader("물품 등록")
        
        with st.form("add_item_form"):
            name = st.text_input("물품명*")
            item_code = st.text_input("품번")
            category = st.text_input("카테고리")
            
            # 거래처 선택 옵션
            supplier_options = ["선택 안함"] + [s['name'] for s in suppliers]
            selected_supplier = st.selectbox("거래처", options=supplier_options)
            
            unit = st.text_input("단위 (예: EA, KG, M 등)")
            stock = st.number_input("초기 재고 수량", value=0.0, step=1.0)
            unit_price = st.number_input("단가", value=0.0, step=100.0)
            description = st.text_area("설명")
            
            submitted = st.form_submit_button("등록")
            
            if submitted:
                # 거래처 ID 설정
                supplier_id = None
                if selected_supplier != "선택 안함":
                    supplier_data = next((s for s in suppliers if s['name'] == selected_supplier), None)
                    if supplier_data:
                        supplier_id = supplier_data['id']
                
                # 새 물품 데이터 구성
                new_item = {
                    'id': generate_id(items),
                    'name': name,
                    'item_code': item_code,
                    'category': category,
                    'supplier_id': supplier_id,
                    'unit': unit,
                    'stock': stock,
                    'unit_price': unit_price,
                    'description': description,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 데이터 유효성 검사
                is_valid, message = validate_item_data(new_item)
                
                if is_valid:
                    items.append(new_item)
                    save_items(items)
                    st.success(f"물품 '{name}'이(가) 등록되었습니다.")
                    # 폼 초기화를 위한 페이지 리로드
                    st.rerun()
                else:
                    st.error(message)
    
    # 대량 등록 탭
    with tab3:
        st.subheader("물품 대량 등록")
        
        # 템플릿 다운로드 옵션
        st.write("물품 대량 등록을 위한 템플릿을 다운로드하세요.")
        
        template_df = pd.DataFrame({
            '물품명': ['물품명을 입력하세요'],
            '품번': ['품번을 입력하세요'],
            '카테고리': ['카테고리를 입력하세요'],
            '거래처명': ['거래처명을 입력하세요 (없으면 비워두세요)'],
            '단위': ['단위를 입력하세요 (예: EA, KG, M)'],
            '초기재고': [0],
            '단가': [0],
            '설명': ['설명을 입력하세요']
        })
        
        template_csv = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="템플릿 CSV 다운로드",
            data=template_csv,
            file_name='items_template.csv',
            mime='text/csv'
        )
        
        # 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("업로드된 데이터 미리보기:")
                st.dataframe(df.head())
                
                if st.button("대량 등록 실행"):
                    # 필수 컬럼 확인
                    if '물품명' not in df.columns:
                        st.error("CSV 파일에 '물품명' 컬럼이 없습니다.")
                    else:
                        # 데이터 변환 및 저장
                        success_count = 0
                        error_count = 0
                        error_messages = []
                        
                        for idx, row in df.iterrows():
                            # 거래처 ID 찾기
                            supplier_id = None
                            if pd.notna(row.get('거래처명', '')) and row.get('거래처명', '') != '':
                                supplier_data = next((s for s in suppliers if s['name'] == row.get('거래처명')), None)
                                if supplier_data:
                                    supplier_id = supplier_data['id']
                            
                            try:
                                stock = float(row.get('초기재고', 0))
                            except:
                                stock = 0
                                
                            try:
                                unit_price = float(row.get('단가', 0))
                            except:
                                unit_price = 0
                                
                            # 새 물품 데이터 구성
                            new_item = {
                                'id': generate_id(items),
                                'name': row.get('물품명', ''),
                                'item_code': row.get('품번', ''),
                                'category': row.get('카테고리', ''),
                                'supplier_id': supplier_id,
                                'unit': row.get('단위', ''),
                                'stock': stock,
                                'unit_price': unit_price,
                                'description': row.get('설명', ''),
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # 데이터 유효성 검사
                            is_valid, message = validate_item_data(new_item)
                            
                            if is_valid:
                                items.append(new_item)
                                success_count += 1
                            else:
                                error_count += 1
                                error_messages.append(f"오류 (행 {idx+2}): {message} - {row.get('물품명', '')}")
                        
                        # 결과 저장 및 표시
                        if success_count > 0:
                            save_items(items)
                            st.success(f"{success_count}개의 물품이 성공적으로 등록되었습니다.")
                        
                        if error_count > 0:
                            st.error(f"{error_count}개의 물품 등록 중 오류가 발생했습니다.")
                            for msg in error_messages:
                                st.warning(msg)
                        
                        # 페이지 리로드
                        if success_count > 0:
                            st.rerun()
                            
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}") 