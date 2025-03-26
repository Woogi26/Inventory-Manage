import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_suppliers, save_suppliers, generate_id, validate_supplier_data

def supplier_management_app():
    st.title("거래처 관리")
    
    # 탭 분리 (조회/등록/수정/삭제)
    tab1, tab2, tab3 = st.tabs(["거래처 목록", "거래처 등록", "대량 등록"])
    
    # 거래처 데이터 로드
    suppliers = load_suppliers()
    
    # 거래처 목록 표시 탭
    with tab1:
        st.subheader("거래처 목록")
        
        # 검색 필터
        search_term = st.text_input("거래처명 검색", "")
        
        filtered_suppliers = suppliers
        if search_term:
            filtered_suppliers = [s for s in suppliers if search_term.lower() in s.get('name', '').lower()]
            
        if filtered_suppliers:
            # DataFrame으로 변환하여 표시
            df = pd.DataFrame(filtered_suppliers)
            # 수정/삭제 버튼을 위한 컬럼 추가
            df = df.drop(columns=['id'], errors='ignore')  # ID 컬럼은 화면에 표시하지 않음
            
            st.dataframe(df)
            
            # 수정/삭제할 거래처 선택
            supplier_names = [s['name'] for s in filtered_suppliers]
            selected_supplier = st.selectbox("수정/삭제할 거래처 선택", supplier_names)
            
            # 선택한 거래처 정보 가져오기
            selected_supplier_data = next((s for s in filtered_suppliers if s['name'] == selected_supplier), None)
            
            if selected_supplier_data:
                edit_col, delete_col = st.columns(2)
                
                with edit_col:
                    if st.button("선택한 거래처 수정"):
                        # 세션 상태에 수정할 거래처 정보 저장
                        st.session_state['edit_supplier'] = selected_supplier_data
                        st.rerun()
                
                with delete_col:
                    if st.button("선택한 거래처 삭제"):
                        # 거래처 삭제 프로세스
                        suppliers = [s for s in suppliers if s['id'] != selected_supplier_data['id']]
                        save_suppliers(suppliers)
                        st.success(f"거래처 '{selected_supplier}'이(가) 삭제되었습니다.")
                        st.rerun()
        else:
            st.info("등록된 거래처가 없습니다.")
        
        # 거래처 수정 폼
        if 'edit_supplier' in st.session_state:
            st.subheader("거래처 정보 수정")
            
            edit_data = st.session_state['edit_supplier']
            
            with st.form("edit_supplier_form"):
                name = st.text_input("거래처명*", edit_data.get('name', ''))
                address = st.text_input("주소", edit_data.get('address', ''))
                phone = st.text_input("연락처", edit_data.get('phone', ''))
                email = st.text_input("이메일", edit_data.get('email', ''))
                note = st.text_area("비고", edit_data.get('note', ''))
                
                submitted = st.form_submit_button("수정 완료")
                
                if submitted:
                    # 수정된 데이터 구성
                    updated_supplier = {
                        'id': edit_data['id'],
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'email': email,
                        'note': note,
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 데이터 유효성 검사
                    is_valid, message = validate_supplier_data(updated_supplier)
                    
                    if is_valid:
                        # 거래처 정보 업데이트
                        for i, s in enumerate(suppliers):
                            if s['id'] == edit_data['id']:
                                suppliers[i] = updated_supplier
                                break
                        
                        save_suppliers(suppliers)
                        st.success(f"거래처 '{name}'의 정보가 수정되었습니다.")
                        
                        # 세션 상태 초기화
                        del st.session_state['edit_supplier']
                        st.rerun()
                    else:
                        st.error(message)
            
            if st.button("수정 취소"):
                del st.session_state['edit_supplier']
                st.rerun()
    
    # 거래처 등록 탭
    with tab2:
        st.subheader("거래처 등록")
        
        with st.form("add_supplier_form"):
            name = st.text_input("거래처명*")
            address = st.text_input("주소")
            phone = st.text_input("연락처")
            email = st.text_input("이메일")
            note = st.text_area("비고")
            
            submitted = st.form_submit_button("등록")
            
            if submitted:
                # 새 거래처 데이터 구성
                new_supplier = {
                    'id': generate_id(suppliers),
                    'name': name,
                    'address': address,
                    'phone': phone,
                    'email': email,
                    'note': note,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 데이터 유효성 검사
                is_valid, message = validate_supplier_data(new_supplier)
                
                if is_valid:
                    suppliers.append(new_supplier)
                    save_suppliers(suppliers)
                    st.success(f"거래처 '{name}'이(가) 등록되었습니다.")
                    # 폼 초기화를 위한 페이지 리로드
                    st.rerun()
                else:
                    st.error(message)
    
    # 대량 등록 탭
    with tab3:
        st.subheader("거래처 대량 등록")
        
        # 템플릿 다운로드 옵션
        st.write("거래처 대량 등록을 위한 템플릿을 다운로드하세요.")
        
        template_df = pd.DataFrame({
            '거래처명': ['거래처명을 입력하세요'],
            '주소': ['주소를 입력하세요'],
            '연락처': ['연락처를 입력하세요'],
            '이메일': ['이메일을 입력하세요'],
            '비고': ['비고 사항을 입력하세요']
        })
        
        template_csv = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="템플릿 CSV 다운로드",
            data=template_csv,
            file_name='suppliers_template.csv',
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
                    if '거래처명' not in df.columns:
                        st.error("CSV 파일에 '거래처명' 컬럼이 없습니다.")
                    else:
                        # 데이터 변환 및 저장
                        success_count = 0
                        error_count = 0
                        error_messages = []
                        
                        for _, row in df.iterrows():
                            new_supplier = {
                                'id': generate_id(suppliers),
                                'name': row.get('거래처명', ''),
                                'address': row.get('주소', ''),
                                'phone': row.get('연락처', ''),
                                'email': row.get('이메일', ''),
                                'note': row.get('비고', ''),
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # 데이터 유효성 검사
                            is_valid, message = validate_supplier_data(new_supplier)
                            
                            if is_valid:
                                suppliers.append(new_supplier)
                                success_count += 1
                            else:
                                error_count += 1
                                error_messages.append(f"오류 (행 {_+2}): {message} - {row.get('거래처명', '')}")
                        
                        # 결과 저장 및 표시
                        if success_count > 0:
                            save_suppliers(suppliers)
                            st.success(f"{success_count}개의 거래처가 성공적으로 등록되었습니다.")
                        
                        if error_count > 0:
                            st.error(f"{error_count}개의 거래처 등록 중 오류가 발생했습니다.")
                            for msg in error_messages:
                                st.warning(msg)
                        
                        # 페이지 리로드
                        if success_count > 0:
                            st.rerun()
                            
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}") 