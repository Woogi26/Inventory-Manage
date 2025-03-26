import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_items, load_bom, save_bom

def bom_management_app():
    st.title("BOM 관리")
    st.write("제품별 BOM(Bill of Materials)을 관리할 수 있습니다.")
    
    # 데이터 로드
    items = load_items()
    bom_data = load_bom()
    
    # 제품 선택
    product_options = [item for item in items]
    
    if not product_options:
        st.warning("등록된 물품이 없습니다. 먼저 물품을 등록해주세요.")
        return
    
    st.subheader("제품 선택")
    
    # 제품 선택 방식 (직접 선택 또는 검색)
    search_term = st.text_input("제품명 검색")
    
    filtered_products = product_options
    if search_term:
        filtered_products = [item for item in product_options if search_term.lower() in item.get('name', '').lower()]
    
    if not filtered_products:
        st.info("검색 결과가 없습니다.")
        return
    
    # 제품 선택 드롭다운
    product_names = [item['name'] for item in filtered_products]
    selected_product_name = st.selectbox("제품 선택", product_names)
    
    # 선택한 제품의 정보 가져오기
    selected_product = next((item for item in items if item['name'] == selected_product_name), None)
    
    if not selected_product:
        st.error("선택한 제품 정보를 찾을 수 없습니다.")
        return
    
    st.write(f"선택한 제품: **{selected_product_name}** (ID: {selected_product['id']})")
    
    # BOM 정보 표시 및 관리
    st.subheader("BOM 구성")
    
    # 선택한 제품의 BOM 정보 가져오기
    product_id_str = str(selected_product['id'])
    components = []
    
    if product_id_str in bom_data:
        components = bom_data[product_id_str]
    
    # 현재 BOM 구성 표시
    if components:
        components_data = []
        
        for component in components:
            material_id = component['material_id']
            material = next((item for item in items if item['id'] == material_id), None)
            
            if material:
                components_data.append({
                    'id': material_id,
                    '자재명': material['name'],
                    '수량': component['quantity'],
                    '단위': material.get('unit', ''),
                    '비고': component.get('note', '')
                })
        
        if components_data:
            st.write("현재 BOM 구성:")
            components_df = pd.DataFrame(components_data)
            st.dataframe(components_df)
    else:
        st.info(f"'{selected_product_name}' 제품의 BOM 정보가 아직 없습니다.")
    
    # BOM 관리 옵션
    st.subheader("BOM 관리 옵션")
    bom_option = st.radio("작업 선택", ["자재 추가", "자재 제거", "자재 수량 수정"])
    
    if bom_option == "자재 추가":
        st.write("자재 추가")
        
        # 추가할 자재 선택 (현재 BOM에 없는 아이템만 표시)
        current_material_ids = [c['material_id'] for c in components]
        available_materials = [item for item in items if item['id'] != selected_product['id'] and item['id'] not in current_material_ids]
        
        if not available_materials:
            st.warning("추가할 수 있는 자재가 없습니다. 모든 자재가 이미 BOM에 포함되어 있거나 자재가 등록되지 않았습니다.")
        else:
            material_options = [f"{item['name']} ({item.get('unit', '')})" for item in available_materials]
            selected_material_option = st.selectbox("자재 선택", material_options)
            selected_material_idx = material_options.index(selected_material_option)
            selected_material = available_materials[selected_material_idx]
            
            quantity = st.number_input("수량", min_value=0.01, value=1.0, step=0.01)
            note = st.text_input("비고")
            
            if st.button("자재 추가"):
                # 새 자재 추가
                new_component = {
                    'material_id': selected_material['id'],
                    'quantity': quantity,
                    'note': note
                }
                
                if product_id_str not in bom_data:
                    bom_data[product_id_str] = []
                
                bom_data[product_id_str].append(new_component)
                save_bom(bom_data)
                
                st.success(f"자재 '{selected_material['name']}'이(가) BOM에 추가되었습니다.")
                st.rerun()
    
    elif bom_option == "자재 제거":
        st.write("자재 제거")
        
        if not components:
            st.warning("BOM에 등록된 자재가 없습니다.")
        else:
            # 제거할 자재 선택
            component_materials = []
            for component in components:
                material = next((item for item in items if item['id'] == component['material_id']), None)
                if material:
                    component_materials.append(material)
            
            material_options = [item['name'] for item in component_materials]
            selected_material_name = st.selectbox("제거할 자재 선택", material_options)
            selected_material = next((item for item in component_materials if item['name'] == selected_material_name), None)
            
            if st.button("자재 제거"):
                # 선택한 자재 제거
                bom_data[product_id_str] = [component for component in components if component['material_id'] != selected_material['id']]
                
                # 자재가 없으면 제품 BOM 항목 자체 제거
                if not bom_data[product_id_str]:
                    del bom_data[product_id_str]
                
                save_bom(bom_data)
                
                st.success(f"자재 '{selected_material_name}'이(가) BOM에서 제거되었습니다.")
                st.rerun()
    
    elif bom_option == "자재 수량 수정":
        st.write("자재 수량 수정")
        
        if not components:
            st.warning("BOM에 등록된 자재가 없습니다.")
        else:
            # 수정할 자재 선택
            component_materials = []
            for component in components:
                material = next((item for item in items if item['id'] == component['material_id']), None)
                if material:
                    component_materials.append({
                        'material': material,
                        'component': component
                    })
            
            material_options = [item['material']['name'] for item in component_materials]
            selected_material_name = st.selectbox("수정할 자재 선택", material_options)
            
            selected_item = next((item for item in component_materials if item['material']['name'] == selected_material_name), None)
            
            if selected_item:
                current_quantity = selected_item['component']['quantity']
                current_note = selected_item['component'].get('note', '')
                
                new_quantity = st.number_input("새 수량", min_value=0.01, value=float(current_quantity), step=0.01)
                new_note = st.text_input("비고", value=current_note)
                
                if st.button("자재 수량 수정"):
                    # 선택한 자재의 수량 수정
                    for component in bom_data[product_id_str]:
                        if component['material_id'] == selected_item['material']['id']:
                            component['quantity'] = new_quantity
                            component['note'] = new_note
                            break
                    
                    save_bom(bom_data)
                    
                    st.success(f"자재 '{selected_material_name}'의 수량이 {new_quantity}로 수정되었습니다.")
                    st.rerun()
    
    # BOM 복사 기능
    st.subheader("BOM 복사")
    st.write("다른 제품의 BOM을 현재 제품으로 복사할 수 있습니다.")
    
    # BOM이 존재하는 제품 목록
    products_with_bom = []
    for pid in bom_data.keys():
        product = next((item for item in items if str(item['id']) == pid), None)
        if product and product['id'] != selected_product['id']:
            products_with_bom.append(product)
    
    if not products_with_bom:
        st.info("복사할 수 있는 다른 제품의 BOM이 없습니다.")
    else:
        source_product_options = [f"{item['name']}" for item in products_with_bom]
        source_product_name = st.selectbox("복사할 BOM 선택", source_product_options)
        source_product = next((item for item in products_with_bom if item['name'] == source_product_name), None)
        
        if source_product:
            copy_mode = st.radio("복사 모드", ["덮어쓰기", "추가"])
            
            if st.button("BOM 복사"):
                source_id_str = str(source_product['id'])
                
                if copy_mode == "덮어쓰기":
                    # 기존 BOM 삭제 후 새로운 BOM으로 대체
                    bom_data[product_id_str] = bom_data[source_id_str].copy()
                else:  # 추가 모드
                    # 기존 BOM에 새로운 항목 추가 (중복 자재는 추가 안함)
                    if product_id_str not in bom_data:
                        bom_data[product_id_str] = []
                    
                    existing_material_ids = [c['material_id'] for c in bom_data[product_id_str]]
                    
                    for component in bom_data[source_id_str]:
                        if component['material_id'] not in existing_material_ids:
                            bom_data[product_id_str].append(component.copy())
                
                save_bom(bom_data)
                st.success(f"'{source_product_name}'의 BOM이 '{selected_product_name}'으로 복사되었습니다.")
                st.rerun() 